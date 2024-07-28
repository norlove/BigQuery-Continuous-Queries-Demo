# BigQuery-Continuous-Queries-Demo
This is an end-to-end demo of using BigQuery continuous queries to address abandoned ecommerce shopping carts.

BigQuery continuous queries are SQL statements that run continuously. Continuous queries let you analyze incoming data in BigQuery in real time. You can insert the output rows produced by a continuous query into a BigQuery table or export them to Pub/Sub or Bigtable. 

Documentation on BigQuery continuous queries can be found [HERE](https://cloud.google.com/bigquery/docs/continuous-queries-introduction), and a blog which provides context of BigQuery continuous queries can be found [TO-BE-ADDED].

----------------------------------------------------------------------------------------------------

Imagine this: You've poured your heart into creating a fantastic product, attracted potential customers to your website, and they've even added items to their cart. But then, they vanish without completing the purchase. Frustrating, right?  Shopping cart abandonment is a widespread issue; the average cart abandonment rate hovers around a disheartening 70% [according to the Baymard Institute](https://baymard.com/lists/cart-abandonment-rate). One solution? Real-time engagement that rekindles their interest with a BigQuery continuous query.

To demonstrate this example, we’ll use a BigQuery table named “abandoned_carts” that logs our website’s abandoned cart events and captures: customer’s contact information, the abandoned cart contents, and the abandonment time. We’ll run a BigQuery continuous query that constantly monitors this “abandoned_carts” table for new events, sends any new abandoned carts through Vertex AI to generate a tailored promotional email for each customer with product suggestions and perhaps a limited-time discount, and publishes the personalized email content to a “recapture_customer” Pub/Sub topic. Lastly we’ll use a simple [Application Integration platform](https://cloud.google.com/application-integration/docs/overview) trigger to send an email for each Pub/Sub message received.

<img width="1022" alt="Screenshot 2024-07-28 at 3 38 17 PM" src="https://github.com/user-attachments/assets/782a51b0-6839-4fa6-b3e5-cce135251c3d">

## Setting up our project

1. Ensure your user account has the appropriate IAM permissions [[ref](https://cloud.google.com/bigquery/docs/continuous-queries#choose_an_account_type)]. During this demo, we'll run the continuous query with a Service Account as we'll be writing to a Pub/Sub topic.

2. Create a dataset and table in your project by running the following SQL query in your BigQuery environment: 
```
#Creates a dataset named Continuous_Queries_demo. Be sure to replace the project production-242320 with your own Project ID.
CREATE SCHEMA `production-242320.Continuous_Queries_Demo`;

#Creates a table named abandoned carts.
CREATE TABLE `Continuous_Queries_Demo.abandoned_carts`(
  customer_name string,
  customer_email string,
  last_updated timestamp default current_timestamp,
  products string);
```
3. Create a BigQuery remote connection in the Cloud Console using [these steps](https://cloud.google.com/bigquery/docs/bigquery-ml-remote-model-tutorial#create_a_cloud_resource_connection).
<img width="544" alt="Screenshot 2024-07-28 at 3 46 08 PM" src="https://github.com/user-attachments/assets/05afada9-a7aa-4cbf-80d6-c075f0a23d4d">

4. Click "Go to connection", and in the Connection Info pane, copy the service account ID for use in the next step.

5. Grant Vertex AI User role IAM access to the service account ID you just copied using [these steps](https://cloud.google.com/bigquery/docs/bigquery-ml-remote-model-tutorial#set_up_access).

6. Create a BigQuery ML remote model by running the following SQL query in your BigQuery environment:
```
#Creates a BigQuery ML remote model named cloud_llm
CREATE OR REPLACE MODEL `Continuous_Queries_Demo.cloud_llm`
REMOTE WITH CONNECTION `production-242320.us.continuous-queries-connection` #swap out the ID of your project
OPTIONS (remote_service_type="CLOUD_AI_LARGE_LANGUAGE_MODEL_V1")
```

7. Create a BigQuery Service Account named "bq-continuous-query-sa", granting yourself permissions to subit a job that runs using the service account [[ref](https://cloud.google.com/bigquery/docs/continuous-queries#user_account_permissions)], and granting permissions to the service account itself to access BigQuery resources [[ref](https://cloud.google.com/bigquery/docs/continuous-queries#service_account_permissions)].

**NOTE: if you have issues with this demo, it is 9 times out of 10 related to an IAM permissions issue.**

8. Create a Pub/Sub topic [[ref](https://cloud.google.com/pubsub/docs/create-topic)] named "recapture_customer", with a default subscription, which you'll write the results of your continuous query to.
<img width="557" alt="Screenshot 2024-07-28 at 4 21 13 PM" src="https://github.com/user-attachments/assets/ce86bcb7-7d22-46d0-8ec3-b904423db1ca">
   
9. Grant the service account you created in step #7 permissions to the Pub/Sub topic with the Pub/Sub Viewer and Pub/Sub Publisher roles [[ref](https://cloud.google.com/bigquery/docs/export-to-pubsub#service_account_permissions_2)].
  
8. BigQuery continuous queries require a BigQuery Enterprise or Enterprise Plus reservation [[ref](https://cloud.google.com/bigquery/docs/continuous-queries-introduction#reservation_limitations)]. Create one now in the US multi-region, with 100 slots, and a 100 slot baseline (at the time of this writing BigQuery continuous queries does not support autoscaling).

<img width="564" alt="Screenshot 2024-07-28 at 4 12 45 PM" src="https://github.com/user-attachments/assets/22d03b1b-0794-4f45-adc6-ba4a8dc4805b">

9. Create a "CONTINUOUS" assignment under your newly created reservation using this SQL statement in the BigQuery editor:
```
CREATE ASSIGNMENT
  `production-242320.region-us.bq-continuous-queries-reservation.continuous-assignment`
OPTIONS (
  assignee = 'projects/production-242320',
  job_type = 'CONTINUOUS');
```

You'll now see your assignment created under your reservation:
<img width="1423" alt="Screenshot 2024-07-28 at 4 18 35 PM" src="https://github.com/user-attachments/assets/35464bff-d47d-4ffb-ae8f-ba8a30331992">


## Create a BigQuery continuous query

1. Paste the following SQL query into your BigQuery environment:
```
EXPORT DATA
 OPTIONS (format = CLOUD_PUBSUB,
 uri = "https://pubsub.googleapis.com/projects/production-242320/topics/recapture_customer")
AS (SELECT
   TO_JSON_STRING(
     STRUCT(
       customer_name AS customer_name,
       customer_email AS customer_email, REGEXP_REPLACE(REGEXP_EXTRACT(ml_generate_text_llm_result,r"(?im)\<html\>(?s:.)*\<\/html\>"), r"(?i)\[your name\]", "Your friends at AI Megastore") AS customer_message))
 FROM ML.GENERATE_TEXT( MODEL `production-242320.Continuous_Queries_Demo.cloud_llm`,
     (SELECT
       customer_name,
       customer_email,
       CONCAT("Write an email to customer ", customer_name, ", explaining the benefits and encouraging them to complete their purchase of: ", products, ". Also show other items the customer might be interested in. Provide the response email in HTML format.") AS prompt
     FROM `production-242320.Continuous_Queries_Demo.abandoned_carts`),
   STRUCT( 1024 AS max_output_tokens,
     0.2 AS temperature,
     1 AS candidate_count,
     TRUE AS flatten_json_output)))
```

2.  You may notice an 
