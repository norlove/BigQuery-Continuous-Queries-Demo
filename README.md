# BigQuery-Continuous-Queries-Demo
This is an end-to-end demo of using BigQuery continuous queries to address abandoned ecommerce shopping carts.

BigQuery continuous queries are SQL statements that run continuously. Continuous queries let you analyze incoming data in BigQuery in real time. You can insert the output rows produced by a continuous query into a BigQuery table or export them to Pub/Sub or Bigtable. 

Documentation on BigQuery continuous queries can be found [HERE](https://cloud.google.com/bigquery/docs/continuous-queries-introduction), and a blog which provides context of BigQuery continuous queries can be found [TBD].

----------------------------------------------------------------------------------------------------

Imagine this: You've poured your heart into creating a fantastic product, attracted potential customers to your website, and they've even added items to their cart. But then, they vanish without completing the purchase. Frustrating, right?  Shopping cart abandonment is a widespread issue; the average cart abandonment rate hovers around a disheartening 70% [according to the Baymard Institute](https://baymard.com/lists/cart-abandonment-rate). One solution? Real-time engagement that rekindles their interest with a BigQuery continuous query.

To demonstrate this example, we’ll use a BigQuery table named “abandoned_carts” that logs our website’s abandoned cart events and captures: customer’s contact information, the abandoned cart contents, and the abandonment time. We’ll run a BigQuery continuous query that constantly monitors this “abandoned_carts” table for new events, sends any new abandoned carts through Vertex AI to generate a tailored promotional email for each customer with product suggestions and perhaps a limited-time discount, and publishes the personalized email content to a “recapture_customer” Pub/Sub topic. Lastly we’ll use a simple [Application Integration platform](https://cloud.google.com/application-integration/docs/overview) trigger to send an email for each Pub/Sub message received.

