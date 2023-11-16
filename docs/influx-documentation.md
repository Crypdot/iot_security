## Setting-up InfluxDB

### Quick guide
1. Install and start influxdb:
 * `sudo apt install influxdb`
 * `sudo service influxdb start`

2. Create a database
 * `curl -i -XPOST http://localhost:8086/query --data-urlencode "q=CREATE DATABASE mqtt"`
 * This creates a database named "mqtt". If not done from the machine hosting influxdb, replace "localhost" with approriate IP address.

3. Modify influx configuration
 * Path `/etc/influxdb/influxdb.conf`, remeber to uncomment changed lines
 * modify `auth-enabled = false` to `true`
 * modify `shared-secret = "mqtt-security"`
 * Save and restart influx service (systemctl or restart machine)

4. Create admin user and a specific user for the database
 * Either install `influxdb-client` or use HTTP requests
 * Use influx CLI: `sudo influx`
 * Select your database: `> USE mqtt`
 * NOTE, must use single quotes when writing passwords!
 * Create admin user with all privileges: `> CREATE USER admin WITH PASSWORD 'admin' WITH ALL PRIVILEGES`
 * Create normal user with write privileges: `> CREATE USER python WITH PASSWORD 'password`
 * Grant privileges to normal user: `> GRANT WRITE ON "mqtt" TO "python"`


### Installing influxdb
`sudo apt install influxdb`

`sudo service influxdb start`

### Creating a database
`curl -i -XPOST http://localhost:8086/query --data-urlencode "q=CREATE DATABASE <database name>"`

Or just make the request with the browser of your choise:
`http://localhost:8086/query?q=CREATE%20DATABASE%20<database name>`

#### Retention policy
The InfluxDB retention enforcement service checks for and removes data with timestamps beyond the defined retention period. A retention policy can be added to a database when creating it: `WITH DURATION <time>`

e.g.: `q=CREATE DATABASE <database name> WITH DURATION 14d`

This would create a database that stores data for 14 days. 

## Using Influx
Influx runs on the port 8086, and it can be used entirely from the influx API. 

The data is stored into specified database, onto a **measurement**. Measurements are similiar to tables in traditional databases. 
Measurements contain **points**, which are data records (rows). Each point:
 * has a measurement, a tag set, a field key, a field value, and a timestamp;
 * is uniquely identified by its series and timestamp.

Tags are similiar to columns. 

Data can be retrieved in JSON format from the databases. 

### Storing data
Storing data can be done through the API's /write function. 

URL: `/write?db=<database name>`

Body: `<measurement>,tag1=value,tag2=value value=[value]`

### Authentication
The data base can be configured to only process requests from authenticated users. Users can have different priviledges e.g. read only. 

To enable authentication, modify Influx's configuration file: `/etc/influxdb/influxdb.conf`

Change line `auth-enabled = false`, to true and uncommen it. It's found under [http] topic. 

#### Creating users
After authentication is enabled, users need to be created. 


Using influx-cli, create admin user with all privileges: `CREATE USER admin WITH PASSWORD '<password>' WITH ALL PRIVILEGES`

Create new users: `CREATE USER <username> WITH PASSWORD '<password>'`

Grant privileges to existing users: `GRANT [READ,WRITE,ALL] ON <database_name> TO <username>`

Credentials can be passed as query parameters or as part of the request body.

`u=<username>&p=<password>`

#### JWT
For a more secure alternative to using passwords, Influx API has functionality for JWT.

Steps to enable:

1. Add a shared secret in your InfluxDB configuration file
2. Generate your JWT token
3. Include the token in HTTP requests

**1.**
In Influx configuration, under [http] topic, set a secret:

`shared-secret = "my super secret pass phrase"`

Alternatively, to avoid keeping your secret phrase as plain text in your InfluxDB configuration file, set the value with the INFLUXDB_HTTP_SHARED_SECRET environment variable.

**2.**
Generate the token using the following format:

`
{
  "username": "myUserName",
  "exp": 1516239022
}
`

 * **username** - The name of your InfluxDB user.
 * **exp** - The expiration time of the token in UNIX epoch time. For increased security, keep token expiration periods short.

Encode the payload using your shared secret. This is done automatically with Python.

The generated token follows this format: `<header>.<payload>.<signature>`

Include your generated token as part of the Authorization header in HTTP requests. Use the Bearer authorization scheme:

`Authorization: Bearer <myToken>`

More on [Influx documentation](https://docs.influxdata.com/influxdb/v1/administration/authentication_and_authorization/#add-a-shared-secret-in-your-influxdb-configuration-file).



### HTTPS
InfluxData strongly recommends enabling HTTPS. 

To enable HTTPS with InfluxDB, you’ll need an existing or new InfluxDB instance and a Transport Layer Security (TLS) certificate (also known as a Secured Sockets Layer (SSL) certificate).

HTTPS can easily be configured form the influxdb configuration, once you have a certificate. 

More on [Influx documentation](https://docs.influxdata.com/influxdb/v1/administration/https_setup/).


### Grafana
Works pretty much out of the box with InfluxDB. After [installing](https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/) Grafana, add your InfluxDB as a data source. Dashboards are ready inside Grafana.