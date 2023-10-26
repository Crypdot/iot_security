## Setting-up InfluxDB

### Installing influxdb
`sudo apt install influxdb`
`sudo service influxdb start`

### Creating a database
`curl -i -XPOST http://localhost:8086/query --data-urlencode "q=CREATE DATABASE [database name]"`

Or just make the request with the browser of your choise:
`http://localhost:8086/query?q=CREATE%20DATABASE%20[database name]`

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

URL: `/write?db=[database name]`

Body: `[measurement],tag1=value,tag2=value value=[value]`