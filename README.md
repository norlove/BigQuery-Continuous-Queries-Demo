# BigQuery-Continuous-Queries-Demo
This is an end-to-end demo using BigQuery continuous queries to address abandoned ecommerce shopping carts. This was demoed onstage at Google Cloud Next 2024 [[recording](https://youtu.be/Zo_y34J16yg?t=1395)].

BigQuery continuous queries are SQL statements that run continuously, allowing you analyze incoming data in BigQuery in real time. You can insert the output rows produced by a continuous query into a BigQuery table or export them to Pub/Sub or Bigtable. 

Documentation on BigQuery continuous queries can be found [HERE](https://cloud.google.com/bigquery/docs/continuous-queries-introduction), and a blog which provides context of BigQuery continuous queries can be found [HERE](https://cloud.google.com/blog/products/data-analytics/bigquery-continuous-queries-makes-data-analysis-real-time).

Be sure to request your project(s) be allowlisted for BigQuery continuous queries by submitting [this request form](https://docs.google.com/forms/d/e/1FAIpQLSc-SL89C9K997jSm_u3oQH-UGGe3brzsybbX6mf5VFaA0a4iA/viewform).

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
3. Create a BigQuery remote connection named "continuous-queries-connection" in the Cloud Console using [these steps](https://cloud.google.com/bigquery/docs/bigquery-ml-remote-model-tutorial#create_a_cloud_resource_connection).

      <img width="544" alt="Screenshot 2024-07-28 at 3 46 08 PM" src="https://github.com/user-attachments/assets/05afada9-a7aa-4cbf-80d6-c075f0a23d4d">

5. After the connection has been created, click "Go to connection", and in the Connection Info pane, copy the service account ID for use in the next step.

6. Grant Vertex AI User role IAM access to the service account ID you just copied using [these steps](https://cloud.google.com/bigquery/docs/bigquery-ml-remote-model-tutorial#set_up_access).

7. Create a BigQuery ML remote model with Gemini 1.5 Pro by running the following SQL query in your BigQuery environment:
      ```
      #Creates a BigQuery ML remote model named gemini_1_5_pro
      CREATE MODEL `Continuous_Queries_Demo.gemini_1_5_pro`
      REMOTE WITH CONNECTION `us.continuous-queries-connection`
      OPTIONS(endpoint = 'gemini-1.5-pro');
      ```

8. Create a BigQuery Service Account named "bq-continuous-query-sa", granting yourself permissions to subit a job that runs using the service account [[ref](https://cloud.google.com/bigquery/docs/continuous-queries#user_account_permissions)], and granting permissions to the service account itself to access BigQuery resources [[ref](https://cloud.google.com/bigquery/docs/continuous-queries#service_account_permissions)].

**NOTE: if you have issues with this demo, it is 9 times out of 10 related to an IAM permissions issue.**

## Setup a Pub/Sub topic

1. Create a Pub/Sub topic [[ref](https://cloud.google.com/pubsub/docs/create-topic)] named "recapture_customer", with a default subscription, which you'll write the results of your continuous query to.
   
      <img width="557" alt="Screenshot 2024-07-28 at 4 21 13 PM" src="https://github.com/user-attachments/assets/ce86bcb7-7d22-46d0-8ec3-b904423db1ca">
   
3. Grant the service account you created in step #7 permissions to the Pub/Sub topic with the Pub/Sub Viewer and Pub/Sub Publisher roles [[ref](https://cloud.google.com/bigquery/docs/export-to-pubsub#service_account_permissions_2)].

## Setup an Application Integration trigger
Google Cloud's [Application Integration platform](https://cloud.google.com/application-integration/docs/overview) offers a comprehensive set of core integration tools to connect and manage the multitude of applications (Google Cloud services and third-party SaaS). We'll use it to create a trigger based on our Pub/Sub topic and send an email based on the contents of the Pub/Sub message.

1. Set up an Application Integration environment by following the [Quick Setup Instructions](https://cloud.google.com/application-integration/docs/setup-application-integration#quick).

2. Once setup, click the CREATE INTEGRATION button and name your integration "abandoned-shopping-carts-integration".
   
      <img width="567" alt="Screenshot 2024-07-28 at 4 35 07 PM" src="https://github.com/user-attachments/assets/fbc79bbe-e8bf-4df9-8c2f-1a7d16fc2e49">

4. Click Triggers at the top of the Application Integration bar, search for "Cloud Pub/Sub", and add your Pub/Sub trigger onto the canvas.

5. Under Trigger Input, add the name of the Pub/Sub Topic and the "bq-continuous-query-sa" service account you previously created.

      <img width="1095" alt="Screenshot 2024-07-28 at 4 39 01 PM" src="https://github.com/user-attachments/assets/de1b3795-a4fa-4bf2-9484-733128204a79">

7. If you see a warning that says "Grant the necessary roles", click GRANT.

8. Click Tasks at the top of the Application Integration bar, search for "Data Mapping", and add the Data Mapping item to your canvas.

9. Connect the Cloud Pub/Sub Trigger to the Data Mapping item.

      <img width="288" alt="Screenshot 2024-07-28 at 4 42 26 PM" src="https://github.com/user-attachments/assets/fd39f8c2-7896-4828-8161-e32a4061bd6c">

10. Click the Data Mapping item and click the button that says "OPEN DATA MAPPING EDITOR"

11. You'll crate four Input variables, each initially starting as "CloudPubSubMessage.data" :

      <img width="1044" alt="Screenshot 2024-07-28 at 4 45 15 PM" src="https://github.com/user-attachments/assets/46546ba1-461a-466f-b7fc-8c4008f1734f">

12. For the first Input's Output, click "create a new one", referring to create a new variable. Name it "message_output", change the Variable Type to "Output from Integration", change the Data Type to "String", and change the default value to "Empty String".

      <img width="567" alt="Screenshot 2024-07-28 at 4 46 41 PM" src="https://github.com/user-attachments/assets/1a81096c-dac7-4946-881b-3be70c2c0d6f">

13. For the second Input, click the Plus icon and select TO_JSON() near the bottom. Click the next Plus and select GET_PROPERTY(), click the "Variable or Value" link, click the Value tab and type in "customer_message". Click Save.

      <img width="1071" alt="Screenshot 2024-07-28 at 4 52 49 PM" src="https://github.com/user-attachments/assets/af0a8a37-22eb-41dd-844a-f89737833435">

14. For the second Input's Output, click "create a new one". Name this one "customer_message" and set the same configuration settings as the "message_output" above.

15. Two of your four data mappings should now be complete

      <img width="1044" alt="Screenshot 2024-07-28 at 4 54 31 PM" src="https://github.com/user-attachments/assets/aab0486c-02ae-477f-bc6d-690282362957">

16. For the third input, click the Plus icon, select TO_JSON, click the next Plus and select GET_PROPERTY(). Click to add a new Value and type in "customer_email". Click Save.

17. For the third Input's Output, click "create a new one". Name this one "customer_email" and set the same configuration settings as the other ones above.

18. For the fourth input, click the Plus icon, select TO_JSON, click the next Plus and select GET_PROPERTY(). Click to add a new Value and type in "customer_name". Click Save.

19. For the fourth Input's Output, click "create a new one". Name this one "customer_name" and set the same configuration settings as the other ones above.

20. All four of your mappings should be complete

      <img width="1448" alt="Screenshot 2024-07-28 at 4 59 21 PM" src="https://github.com/user-attachments/assets/3741cb2a-7b18-4fbd-977d-77af56a94eef">

21. To the left of "Data Mapping Task Editor" on the top of the screen, click the back arrow to go back to the canvas.

22. Click Tasks at the top of the Application Integration bar, search for "Send Email", and add the Send Email item to your canvas.

23. Connect the Data Mapping item to the Send Email item.

      <img width="253" alt="Screenshot 2024-07-28 at 5 02 11 PM" src="https://github.com/user-attachments/assets/a7de33fb-3833-4562-915b-473afde39f65">

24. Click the Send Email item and on for Task Input enter the following:
    - To Recipient(s) -> Click "Variable" and search for "customer_email"
    - Subject -> Type in "Don't forget the items in your cart"
    - Body Format -> HTML
    - Body in Plain Text -> Click "Variable" and search for "customer_message"

      <img width="396" alt="Screenshot 2024-07-28 at 5 06 21 PM" src="https://github.com/user-attachments/assets/41808d47-9065-44e1-91fe-c2593598a509">

25. Click the "PUBLISH" button on the top right of the Application Integration bar

      <img width="1491" alt="Screenshot 2024-07-28 at 5 07 00 PM" src="https://github.com/user-attachments/assets/9bc2e49d-fa52-4642-8aa6-0da03aee9e72">

26. Go back to the Pub/Sub page and to your Pub/Sub Topic named "recapture_customer", which we created earlier. You'll see that you have a new subscription named something like "<your_project_name>_recapture_customer_<some_random_string>"

      <img width="1353" alt="Screenshot 2024-07-29 at 1 19 41 AM" src="https://github.com/user-attachments/assets/99df906d-f6f7-446c-bea7-55b47b57fd1f">

27. Click on this subscription, then click the Edit pencil button at the top of the screen.

28. Under the Service Account section, you'll likely see a warning which states "Note: Cloud Pub/Sub needs the role roles/iam.serviceAccountTokenCreator granted to service account service-<your_project_number>@gcp-sa-pubsub.iam.gserviceaccount.com on this project to create identity tokens. You can change this later."

      <img width="566" alt="Screenshot 2024-07-29 at 1 22 23 AM" src="https://github.com/user-attachments/assets/7f167d46-f3fd-4d7b-be7d-4168d23e85ac">

29. Click the "GRANT" button to grant these permissions. Then click the "UPDATE" button at the bottom of the Edit wizard.

24. Your Application Integration should now be fully deployed.

      <img width="1485" alt="Screenshot 2024-07-28 at 5 08 18 PM" src="https://github.com/user-attachments/assets/23b493b0-595a-4d51-8b72-59547faef211">

## Create a BigQuery continuous query

1. BigQuery continuous queries require a BigQuery Enterprise or Enterprise Plus reservation [[ref](https://cloud.google.com/bigquery/docs/continuous-queries-introduction#reservation_limitations)]. Create one now named "bq-continuous-queries-reservation" in the US multi-region, with 100 slots, and a 100 slot baseline (at the time of this writing BigQuery continuous queries does not support autoscaling).

      <img width="564" alt="Screenshot 2024-07-28 at 4 12 45 PM" src="https://github.com/user-attachments/assets/22d03b1b-0794-4f45-adc6-ba4a8dc4805b">

2. Once the reservation has been created, click on the three dots under Actions, and click "Create assignment". 

      <img width="212" alt="Screenshot 2024-08-01 at 6 26 21 PM" src="https://github.com/user-attachments/assets/2d71fe08-d3c0-4d35-ab4a-769120f535e4">

3. Click Browse and find the project you are using for this demo. Then Select "CONTINUOUS" as the Job Type. Click Create.

      <img width="558" alt="Screenshot 2024-08-01 at 6 27 59 PM" src="https://github.com/user-attachments/assets/8f455be4-5fd1-469c-be3f-e3f3e3d43133">

**NOTE: If you do not see this option, your project or user may not be allowlisted to use the BigQuery continuous queries public preview. Fill out [this request form](https://docs.google.com/forms/d/e/1FAIpQLSc-SL89C9K997jSm_u3oQH-UGGe3brzsybbX6mf5VFaA0a4iA/viewform) to obtian access.**

4. You'll now see your assignment created under your reservation:

      <img width="1423" alt="Screenshot 2024-07-28 at 4 18 35 PM" src="https://github.com/user-attachments/assets/35464bff-d47d-4ffb-ae8f-ba8a30331992">

5. Go back to the BigQuery SQL editor and paste the following SQL query:
      ```
      EXPORT DATA
       OPTIONS (format = CLOUD_PUBSUB,
       uri = "https://pubsub.googleapis.com/projects/production-242320/topics/recapture_customer")
      AS (SELECT
         TO_JSON_STRING(
           STRUCT(
             customer_name AS customer_name,
             customer_email AS customer_email, REGEXP_REPLACE(REGEXP_EXTRACT(ml_generate_text_llm_result,r"(?im)\<html\>(?s:.)*\<\/html\>"), r"(?i)\[your name\]", "Your friends at AI Megastore") AS customer_message))
       FROM ML.GENERATE_TEXT( MODEL `Continuous_Queries_Demo.gemini_1_5_pro`,
           (SELECT
             customer_name,
             customer_email,
             CONCAT("Write an email to customer ", customer_name, ", explaining the benefits and encouraging them to complete their purchase of: ", products, ". Also show other items the customer might be interested in. Provide the response email in HTML format.") AS prompt
           FROM `Continuous_Queries_Demo.abandoned_carts`),
         STRUCT( 1024 AS max_output_tokens,
           0.2 AS temperature,
           1 AS candidate_count, 
           TRUE AS flatten_json_output)))
      ```

6.  Before you can run your query, you must enable BigQuery continuous query mode. In the BigQuery editor, click More -> Continuous Query mode

      <img width="1143" alt="Screenshot 2024-08-01 at 6 31 38 PM" src="https://github.com/user-attachments/assets/a9e0db6b-2d5f-4048-92c8-68419b7f603f">

7. When the window opens, click the button CONFIRM to enable continuous queries for this BigQuery editor tab.

6. Since we are writing the results of this continuous query to a Pub/Sub topic, you must run this query using a Service Account [[ref](https://cloud.google.com/bigquery/docs/continuous-queries#choose_an_account_type)]. We'll use the service account we created earlier. Click More -> Query Settings and scroll down to the Continuous query section and select your service account "bq-continuous-query-sa" and click Save.

      <img width="551" alt="Screenshot 2024-07-29 at 12 03 55 AM" src="https://github.com/user-attachments/assets/28aff716-a3b9-4c85-a829-33efed32cd03">

7. Your continuous query should now be valid.

      <img width="240" alt="Screenshot 2024-08-01 at 6 33 50 PM" src="https://github.com/user-attachments/assets/fbc3af67-7372-457f-8939-f4d71d313687">

8. Click Run to start your continuous query. After about a minute or so, the continuous query will be fully running, ready to receive and process incoming data into your abandoned_carts table.
   
## Stream data into the Abandoned Carts BigQuery table

1. BigQuery continuous queries can read and process data which arrives into BigQuery in a variety of ways [[ref](https://cloud.google.com/bigquery/docs/continuous-queries-introduction)]. For the purposes of this end-to-end demo, we'll offer two options: a very simple DML INSERT and streaming data to the abandoned_carts table using the BigQuery Storage Write API.

2. To insert data into your table via a simple DML INSERT, just run the below query from the BigQuery console to insert one new row into your table:
      ```
      #Simple DML INSERT to add one "abandoned shopping cart" to your table. 
      #Be sure to change the email address to an email address you can actually access for demo purposes.
      INSERT INTO `Continuous_Queries_Demo.abandoned_carts`(customer_name, customer_email,products)
      VALUES ("Your_Shopper's_Name","Your.Shoppers.Email@gmail.com","Violin Strings, Tiny Saxophone, Guitar Strap")
      ```

3. To stream data into your table via the BigQuery Storage Write API [[ref](https://cloud.google.com/bigquery/docs/write-api)], copy the files from the write-api-streaming-example folder from this GitHub repo into a Unix-based development environment (the [Google Cloud Shell](https://cloud.google.com/shell) is amazing for simple dev/test like this)

4. In this example, we’ll use Python, so we’ll stream data as protocol buffers. For a quick refresher on working with protocol buffers, [here’s a great tutorial](https://developers.google.com/protocol-buffers/docs/pythontutorial). Using Python, we’ll first align our protobuf messages to the table we created using a .proto file in proto2 format. Use the sample_data.proto file from the write-api-streaming-example folder you downloaded to your developer environment, then run the following command within to update your protocol buffer definition:
      ```
      protoc --python_out=. sample_data.proto
      ```

5. Within your developer environment, run this sample streaming_script.py Python script to insert some new example abandoned cart events by reading from the abandoned_carts.json file and writing into the abandoned_carts BigQuery table. This code uses the BigQuery Storage Write API to stream a batch of row data by appending proto2 serialized bytes to the serialzed_rows repeated field like the example below:
      ```
      row = sample_data_pb2.SampleData()
          row.customer_name = "Your_Shopper's_Name"
          row.customer_email = “Your.Shoppers.Email@gmail.com”
          row.products = "Violin Strings, Tiny Saxophone, Guitar Strap"
      proto_rows.serialized_rows.append(row.SerializeToString())
      ```

6. Within your BigQuery abandoned_carts table, you'll see your newly ingested data:

      <img width="1093" alt="Screenshot 2024-07-29 at 1 34 45 AM" src="https://github.com/user-attachments/assets/cf82e9f6-0033-44f4-ba5b-cae8a1bc7507">

7. Now go check your email for the personalized message(s)!

      ![Screenshot 2024-08-01 at 7 02 02 PM](https://github.com/user-attachments/assets/2a03c059-1ae7-43ee-a0ca-acf146dda41c)
