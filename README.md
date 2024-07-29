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

## Setup a Pub/Sub topic

1. Create a Pub/Sub topic [[ref](https://cloud.google.com/pubsub/docs/create-topic)] named "recapture_customer", with a default subscription, which you'll write the results of your continuous query to.
<img width="557" alt="Screenshot 2024-07-28 at 4 21 13 PM" src="https://github.com/user-attachments/assets/ce86bcb7-7d22-46d0-8ec3-b904423db1ca">
   
2. Grant the service account you created in step #7 permissions to the Pub/Sub topic with the Pub/Sub Viewer and Pub/Sub Publisher roles [[ref](https://cloud.google.com/bigquery/docs/export-to-pubsub#service_account_permissions_2)].

## Setup an Application Integration trigger
Google Cloud's [Application Integration platform](https://cloud.google.com/application-integration/docs/overview) offers a comprehensive set of core integration tools to connect and manage the multitude of applications (Google Cloud services and third-party SaaS). We'll use it to create a trigger based on our Pub/Sub topic and send an email based on the contents of the Pub/Sub message.

1. Set up an Application Integration environment by following the [Quick Setup Instructions](https://cloud.google.com/application-integration/docs/setup-application-integration#quick).

2. Once setup, click the CREATE INTEGRATION button and name your integration "abandoned-shopping-carts-integration".
<img width="567" alt="Screenshot 2024-07-28 at 4 35 07 PM" src="https://github.com/user-attachments/assets/fbc79bbe-e8bf-4df9-8c2f-1a7d16fc2e49">

3. Click Triggers at the top of the Application Integration bar, search for "Cloud Pub/Sub", and add your Pub/Sub trigger onto the canvas.

4. Under Trigger Input, add the name of the Pub/Sub Topic and the "bq-continuous-query-sa" service account you previously created.
<img width="1095" alt="Screenshot 2024-07-28 at 4 39 01 PM" src="https://github.com/user-attachments/assets/de1b3795-a4fa-4bf2-9484-733128204a79">

5. If you see a warning that says "Grant the necessary roles", click GRANT.

6. Click Tasks at the top of the Application Integration bar, search for "Data Mapping", and add the Data Mapping item to your canvas.

7. Connect the Cloud Pub/Sub Trigger to the Data Mapping item.
<img width="288" alt="Screenshot 2024-07-28 at 4 42 26 PM" src="https://github.com/user-attachments/assets/fd39f8c2-7896-4828-8161-e32a4061bd6c">

8. Click the Data Mapping item and click the button that says "OPEN DATA MAPPING EDITOR"

9. You'll crate four Input variables, each initially starting as "CloudPubSubMessage.data" :
<img width="1044" alt="Screenshot 2024-07-28 at 4 45 15 PM" src="https://github.com/user-attachments/assets/46546ba1-461a-466f-b7fc-8c4008f1734f">

10. For the first Input's Output, click "create a new one", referring to create a new variable. Name it "message_output", change the Variable Type to "Output from Integration", change the Data Type to "String", and change the default value to "Empty String".
<img width="567" alt="Screenshot 2024-07-28 at 4 46 41 PM" src="https://github.com/user-attachments/assets/1a81096c-dac7-4946-881b-3be70c2c0d6f">

11. For the second Input, click the Plus icon and select TO_JSON() near the bottom. Click the next Plus and select GET_PROPERTY(), click the "Variable or Value" link, click the Value tab and type in "customer_message". Click Save.
<img width="1071" alt="Screenshot 2024-07-28 at 4 52 49 PM" src="https://github.com/user-attachments/assets/af0a8a37-22eb-41dd-844a-f89737833435">

12. For the second Input's Output, click "create a new one". Name this one "customer_message" and set the same configuration settings as the "message_output" above.

13. Two of your four data mappings should now be complete
<img width="1044" alt="Screenshot 2024-07-28 at 4 54 31 PM" src="https://github.com/user-attachments/assets/aab0486c-02ae-477f-bc6d-690282362957">

14. For the third input, click the Plus icon, select TO_JSON, click the next Plus and select GET_PROPERTY(). Click to add a new Value and type in "customer_email". Click Save.

15. For the third Input's Output, click "create a new one". Name this one "customer_email" and set the same configuration settings as the other ones above.

16. Fir the fourth input, click the Plus icon, select TO_JSON, click the next Plus and select GET_PROPERTY(). Click to add a new Value and type in "customer_name". Click Save.

17. For the fourth Input's Output, click "create a new one". Name this one "customer_name" and set the same configuration settings as the other ones above.

18. All four of your mappings should be complete
<img width="1448" alt="Screenshot 2024-07-28 at 4 59 21 PM" src="https://github.com/user-attachments/assets/3741cb2a-7b18-4fbd-977d-77af56a94eef">

19. To the left of "Data Mapping Task Editor" on the top of the screen, click the back arrow to go back to the canvas.

20. Click Tasks at the top of the Application Integration bar, search for "Send Email", and add the Send Email item to your canvas.

21. Connect the Data Mapping item to the Send Email item.
<img width="253" alt="Screenshot 2024-07-28 at 5 02 11 PM" src="https://github.com/user-attachments/assets/a7de33fb-3833-4562-915b-473afde39f65">

22. Click the Send Email item and on for Task Input enter the following:
    To Recipient(s) -> Click "Variable" and search for "customer_email"
    Subject -> Type in "Don't forget the items in your cart"
    Body Format -> HTML
    Body in Plain Text -> Click "Variable" and search for "customer_message"
<img width="396" alt="Screenshot 2024-07-28 at 5 06 21 PM" src="https://github.com/user-attachments/assets/41808d47-9065-44e1-91fe-c2593598a509">

23. Click the "PUBLISH" button on the top right of the Application Integration bar
<img width="1491" alt="Screenshot 2024-07-28 at 5 07 00 PM" src="https://github.com/user-attachments/assets/9bc2e49d-fa52-4642-8aa6-0da03aee9e72">

24. Your Application Integration should now be fully deployed.
<img width="1485" alt="Screenshot 2024-07-28 at 5 08 18 PM" src="https://github.com/user-attachments/assets/23b493b0-595a-4d51-8b72-59547faef211">

## Create a BigQuery continuous query

1. BigQuery continuous queries require a BigQuery Enterprise or Enterprise Plus reservation [[ref](https://cloud.google.com/bigquery/docs/continuous-queries-introduction#reservation_limitations)]. Create one now in the US multi-region, with 100 slots, and a 100 slot baseline (at the time of this writing BigQuery continuous queries does not support autoscaling).

<img width="564" alt="Screenshot 2024-07-28 at 4 12 45 PM" src="https://github.com/user-attachments/assets/22d03b1b-0794-4f45-adc6-ba4a8dc4805b">

2. Create a "CONTINUOUS" assignment under your newly created reservation using this SQL statement in the BigQuery editor:
```
CREATE ASSIGNMENT
  `production-242320.region-us.bq-continuous-queries-reservation.continuous-assignment`
OPTIONS (
  assignee = 'projects/production-242320',
  job_type = 'CONTINUOUS');
```

You'll now see your assignment created under your reservation:
<img width="1423" alt="Screenshot 2024-07-28 at 4 18 35 PM" src="https://github.com/user-attachments/assets/35464bff-d47d-4ffb-ae8f-ba8a30331992">

3. Paste the following SQL query into your BigQuery environment:
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

4.  You may notice an 
