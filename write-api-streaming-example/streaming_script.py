# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
# This code sample demonstrates using the low-level generated client for Python.
# Make sure you provide your Project, Dataset, and Table details below in line 122.
 
from google.cloud import bigquery_storage_v1
from google.cloud.bigquery_storage_v1 import types
from google.cloud.bigquery_storage_v1 import writer
from google.protobuf import descriptor_pb2
import logging
import json
 
##################################################################################
# To update your protocol buffer definition with your sample_data.proto file run:
#
#   protoc --python_out=. sample_data.proto
#
##################################################################################
 
import sample_data_pb2
 
# The list of fields (i.e. the table's schema) to search in the given data to write to BigQuery.
FIELDS_TO_CHECK = [
    "customer_name",
    "customer_email",
    "products"]
 
# Function to create a batch of row data to be serialized.
def create_row_data(data):
    row = sample_data_pb2.SampleData()
    for field in FIELDS_TO_CHECK:
      # This IF statement is particularly useful when optional fields aren't provided and thus are passed
      # as null values to BigQuery.
      if field in data:
        setattr(row, field, data[field])
    return row.SerializeToString()
 
 
class BigQueryStorageWriteAppend(object):
 
    # Use the Storage Write API default stream to stream data into BigQuery.
    # This mode uses at-least once delivery
    # The stream name is: projects/{project}/datasets/{dataset}/tables/{table}/_default
    def append_rows_proto2(
        project_id: str, dataset_id: str, table_id: str, data: dict
    ):
 
        write_client = bigquery_storage_v1.BigQueryWriteClient()
        parent = write_client.table_path(project_id, dataset_id, table_id)
        stream_name = f'{parent}/_default'
        write_stream = types.WriteStream()
 
        # Create a template with fields needed for the first request.
        request_template = types.AppendRowsRequest()
 
        # The request must contain the stream name.
        request_template.write_stream = stream_name
 
        # So that BigQuery knows how to parse the serialized_rows, generate a
        # protocol buffer representation of your message descriptor.
        proto_schema = types.ProtoSchema()
        proto_descriptor = descriptor_pb2.DescriptorProto()
        sample_data_pb2.SampleData.DESCRIPTOR.CopyToProto(proto_descriptor)
        proto_schema.proto_descriptor = proto_descriptor
        proto_data = types.AppendRowsRequest.ProtoData()
        proto_data.writer_schema = proto_schema
        request_template.proto_rows = proto_data
 
        # Some stream types support an unbounded number of requests. Construct an
        # AppendRowsStream to send an arbitrary number of requests to a stream.
        append_rows_stream = writer.AppendRowsStream(write_client, request_template)
 
        # Calls the create_row_data function to append proto2 serialized bytes to the
        # serialized_rows repeated field.
        proto_rows = types.ProtoRows()
        for row in data:
            proto_rows.serialized_rows.append(create_row_data(row))
 
        # Appends data to the given stream.
        request = types.AppendRowsRequest()
        proto_data = types.AppendRowsRequest.ProtoData()
        proto_data.rows = proto_rows
        request.proto_rows = proto_data
 
        append_rows_stream.send(request)
 
        print(f"Rows to table: '{parent}' have been written.")
 
 
if __name__ == "__main__":
 
    ###### Uncomment the below block to provide additional logging capabilities ######
    #logging.basicConfig(
    #    level=logging.DEBUG,
    #    format="%(asctime)s [%(levelname)s] %(message)s",
    #    handlers=[
    #        logging.StreamHandler()
    #    ]
    #)
    ###### Uncomment the above block to provide additional logging capabilities ######
 
    with open('abandoned_carts.json', 'r') as json_file:
        data = json.load(json_file)
    BigQueryStorageWriteAppend.append_rows_proto2("production-242320","Continuous_Queries_Demo", "abandoned_carts",data=data) # Change this to your specific BigQuery project, dataset, table details
