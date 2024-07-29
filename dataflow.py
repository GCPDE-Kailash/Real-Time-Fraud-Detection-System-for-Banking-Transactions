import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions, StandardOptions
from apache_beam.io import ReadFromPubSub, WriteToBigQuery
import json
import os

# Set the Google Cloud credentials environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "df-pipeline-project-sa-authentication_key.json"

# Create the PipelineOptions object and configure it
pipeline_options = PipelineOptions()
pipeline_options.view_as(SetupOptions).save_main_session = True
pipeline_options.view_as(StandardOptions).streaming = True

class FraudDetection(beam.DoFn):
    def process(self, element):
        # Parse the JSON element
        transaction = json.loads(element)
        transaction_amount = transaction['amount']
        
        # Apply the fraud detection rule
        if transaction_amount > 10000:  # Example fraud detection rule
            transaction['fraud_flag'] = True
        else:
            transaction['fraud_flag'] = False
        
        # Yield the processed transaction
        yield transaction

def run():
    # Initialize the pipeline with the configured options
    p = beam.Pipeline(options=pipeline_options)

    (p 
     # Read messages from the Pub/Sub subscription
     | 'ReadFromPubSub' >> ReadFromPubSub(subscription='projects/df-pipeline-project-19062024/subscriptions/banking-sub')
     # Apply a global window with a trigger to process messages every 60 seconds
     | 'WindowInto' >> beam.WindowInto(
            windowfn=beam.transforms.window.GlobalWindows(), 
            trigger=beam.transforms.trigger.AfterProcessingTime(60),
            accumulation_mode=beam.transforms.trigger.AccumulationMode.DISCARDING
        )
     # Apply the fraud detection transformation
     | 'FraudDetection' >> beam.ParDo(FraudDetection())
     # Write the processed transactions to BigQuery
     | 'WriteToBigQuery' >> WriteToBigQuery(
            table='df-pipeline-project-19062024:banking_fraud.transactions_tbl3', #only need create dataset in bq
            schema='transaction_id:STRING, account_number:STRING, amount:FLOAT, timestamp:TIMESTAMP, fraud_flag:BOOLEAN',
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            custom_gcs_temp_location='gs://folder-temp/temp'
        )
    )

    # Run the pipeline and wait until it finishes
    p.run().wait_until_finish()

# Run the pipeline if this script is executed directly
if __name__ == '__main__':
    run()
