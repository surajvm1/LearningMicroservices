## Project Overview

- Initial intention (rough): 
  - We must have 2 applications say: `businessMicroservice` and `consumerMicroservice`. 
  - Consider having the following db containers running as well locally: `postgresql`, `redis`, `mongodb`, etc.
  - `businessMicroservice` should have endpoints which check the health of db containers, query over tables in the db's, and have the ability to perform basic CRUD operations. 
  - Containerize the application. 
  - We should be able to spin up multiple instances of the microservice running on different ports. There should be APIs which capture status of another port from a given port.
  - Later, `consumerMicroservice` should be designed to mimic how a user/entity would interact with APIs in `businessMicroservice`. In short, allow 2 microservices to communicate with one another. 
  - Try running `businessMicroservice` in 2 container instances in different ports. And then your `consumerMicroservice` should send request to each of the running containers of `businessMicroservice` in round-robin fashion, kind of acting like a load balancer.
  - More tasks defined in the project as we go down... 

- Long term goal (brief)
  - The complexity of project will increase with time. We will have more scenarios to cover like: complicating APIs; publishing data to Kafka/Flink; having Debezium setup to capture CDC once we update postgres tables via our microservices, etc. Objective is to mimic how production systems work as closely as possible. Once, we are set locally, we can try running the infra on cloud systems.   

**Note**: Some major errors I encountered, learnings, blogs/videos, little help from chatgpt in understanding concepts I have attached at the bottom of the Readme for reference. The code written in the project is covered with comments for easy-understanding. To understand the project one may have to oscillate between code comments and info in tasks in Readme. 

------------------------------------------------------

### Steps followed (Flow) in project: 

#### Basic setup: 

Locally, created a directory called: `fastapiproject/` to have all project files saved. Necessary installations (mac):

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\
brew install pyenv
pyenv install 3.10.6
python3
pyenv versions
```

Ensure you have `pip` package manager installed and docker/podman installed to run containers. 
In this exercise, I have used docker in the beginning later switched to podman (Note all docker commands run same in podman, except instead of using `docker` keyword, use `podman` in commands)
So do install docker, docker desktop, podman, docker compose, podman compose (compose utilities are different and should be installed separately - we learn more about them later)

Create 2 folders or virtual environments where we will have our code: 
`python3 -m venv consumerMicroservice`
`python3 -m venv businessMicroservice`

Ensure env is clean by checking installed packages:
`pip list`

Before starting project my Py version: Python 3.9.6
(Not sure why, but Py 3.10.6 was not installing, so went ahead with 3.9.6 for now)

We will work around developing `businessMicroservice` so activate the env. We can also activate `consumerMicroservice` though not using it now. 
Open 2 terminals and `cd` into the directory for business & consumer service and activate the env. 
In my case: (Eg)
- `cd /Users/suraj/Desktop/projectsSimpl/fastapiproject/fapi/consumerMicroservice`, and then: `source bin/activate`
- `cd /Users/suraj/Desktop/projectsSimpl/fastapiproject/fapi/businessMicroservice`, and then: `source bin/activate`

Current focus is on developing `businessMicroservice`. Activate the venv (as shown above and then):

Installing few packages: 

```
pip install fastapi requests "uvicorn[standard]" SQLAlchemy==1.4.46 psycopg2-binary pydantic pandas redis
```

Exporting the installed packages/dependencies in env in a requirements.txt file: `pip freeze > requirements.txt`

My current snapshot of packages on my local based on commands ran earlier: 

```
annotated-types==0.5.0
anyio==3.7.1
async-timeout==4.0.3
certifi==2024.6.2
charset-normalizer==3.3.2
click==8.1.7
exceptiongroup==1.2.1
fastapi==0.103.2
greenlet==3.0.3
h11==0.14.0
httptools==0.6.0
idna==3.7
importlib-metadata==6.7.0
numpy==1.21.6
pandas==1.3.5
psycopg2-binary==2.9.9
pydantic==2.5.3
pydantic_core==2.14.6
python-dateutil==2.9.0.post0
python-dotenv==0.21.1
pytz==2024.1
PyYAML==6.0.1
redis==5.0.6
requests==2.31.0
six==1.16.0
sniffio==1.3.1
SQLAlchemy==1.4.46
starlette==0.27.0
typing_extensions==4.7.1
urllib3==2.0.7
uvicorn==0.22.0
uvloop==0.18.0
watchfiles==0.20.0
websockets==11.0.3
zipp==3.15.0
```

We could have also defined packages in the txt file first and then run `pip install -r requirements.txt`. 

Create core logic files (created main & app py files): `touch main.py app.py`

Writing boilerplate fastapi code in `main.py`: 

```
Core logic: 
@app.get("/")
def health_check_root_endpoint():
    return {"Health check: main.py root server"}
```

My current dir (got my running `pwd` in terminal): `/Users/suraj/Desktop/projectsSimpl/fastapiproject/fapi/businessMicroservice`. 

- To run the app server on a port 8000 command used in env terminal: `uvicorn app:app --port 8000 --reload`. Note in this case, the path where you execute the command and the file path are same.
- Assume you are in a different path and want to run the server, it can also be done (same I have done here for learning purposes in this repo); To run the main app server on a port 8001 command used in env terminal: `uvicorn sampleService.main:app --port 8001 --reload`. You use `.` operator to give the path. 

As we see, the app is running up on a server we defined. 

![fastapi app server running](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/4serverhealthy.png)

#### **Task1**: Write a logic wherein when you hit an endpoint of app running on port 8000, it returns the health status of app running on port 8001? 

Core logic:
``` 
@app.get("/mainappstatus")
def read_root():
    url = 'http://127.0.0.1:8001/currentStatus' # Note that endpoint is camelCase, same is expected when typing in url/testing via postman
    response = requests.get(url)
    print(f"Status of main app server: {response.status_code}")
    data = json.loads(response.text)
    return data
```

Note: I start both the app/main servers in different ports 8000, 8001 and ensure they are running to be able to properly test code, by running previous commands (uvicorn commands) as shown earlier.

#### **Task1.1**: Setup Redis and Postgresql locally via docker?  

Setting Redis locally via docker using commands: Note that in below command I am using port mapping `7001:6379`, i.e will run the Redis container on a different port 7001 rather than default port 6379 (in a rough way for now). To be more technical (which we will again revisit and understand in later parts):
- We are using concept of port mapping; So this flag maps port 6379 inside the container (the default port Redis listens on) to port 7001 on the host machine. This allows you to connect to Redis on your host machine using localhost:7001.
- When we type `http://localhost:7001/` in our browser or postman, we won't get any response though as it (Redis) is a database server, not a web server. Redis container listens for database connections on its port (in this case, 6379 mapped to 7001), but it does not serve web pages or respond to HTTP requests.

```
docker run --name redislocal -p 7001:6379 redis 
docker exec -it redislocal redis-cli # inside the container 

# Similar to docker, we can also use podman; like: 
## podman run --name redislocal -p 7001:6379 redis
## podman exec -it redislocal redis-cli    

Commands to execute inside redis container to setup/play around: 
127.0.0.1:6379> set name "suraj"
OK
127.0.0.1:6379> get name
"suraj"
127.0.0.1:6379> set nametemp "srjv" EX 10
OK
127.0.0.1:6379> get nametemp
"srjv"
127.0.0.1:6379> get nametemp
(nil)
127.0.0.1:6379> exists name
(integer) 1
127.0.0.1:6379> del name
(integer) 1
127.0.0.1:6379> exists name
(integer) 0
127.0.0.1:6379> append name "verma"
(integer) 5
127.0.0.1:6379> get name
"verma"
127.0.0.1:6379> append name "ABC"
(integer) 8
127.0.0.1:6379> get name
"vermaABC"
127.0.0.1:6379(subscribed mode)> subscribe tempstream
1) "subscribe"
2) "tempstream"
3) (integer) 1
4) "message"
5) "tempstream"
127.0.0.1:6379> publish tempstream "learning redis..."
(integer) 1
You cannot publish if no subscribers
127.0.0.1:6379> info server

# stopping and starting redis container 
docker stop 4c3199c94903
docker stop redislocal (or) podman stop redislocal
docker start redislocal (or) podman start redislocal

# to get the version or details of the container use: docker inspect redislocal (or) podman inspect redislocal
We get version is, apart from other details (as I am doing the project): "REDIS_VERSION=7.2.4"
```

Setting up Postgresql locally via docker using commands: 

```
docker run --name postgreslocal -p 7002:5432  -e POSTGRES_PASSWORD=1234 -e POSTGRES_USER=postgresdockerlocal postgres 
# Note that -e key in command means env variable, if you add -d in the command, the terminal will run in detached mode - so in background all postgresql setup commands would run and you can continue using same terminal

We can also use podman instead of docker; simply: 
podman run --name postgreslocal -p 7002:5432  -e POSTGRES_PASSWORD=1234 -e POSTGRES_USER=postgresdockerlocal postgres

Commands to run inside postgres container to setup/play around: 
docker exec -it postgreslocal bash # to get into container of postgres, we have named container postgreslocal as we know
## Or to use podman: podman exec -it postgreslocal bash

root@e4fb5a81ca46:/# psql -U postgresdockerlocal # we know the user name is postgresdockerlocal. Connect to the database as the user username instead of the default.

## Creating a database, later we create tables inside it
postgresdockerlocal-# create database fapidb; 
## Note that the semi colon is very important when you execute the commands else it wont work
## Also to enter the database shell directly from user you can use (else below commands for step-by-step understanding): `psql -U postgresdockerlocal -d fapidb`

# Creating another user and trying to create tables/db using that 
postgresdockerlocal-# CREATE USER postgresdluser WITH PASSWORD '1234'; 
## Note: I have observed in postgresql docker container after executing command, execute it 2-3 times as the shell seems to be not listening very well. Also, sometimes, it doesn't sync well, so better exit the container and enter again for changes to work

postgresdockerlocal=# \du ## Note that \q will exit session
List of roles
      Role name      |                         Attributes                         
---------------------+------------------------------------------------------------
 postgresdluser      | 
 postgresdockerlocal | Superuser, Create role, Create DB, Replication, Bypass RLS
 
## Giving all necessary permissions to our new user which we use to create tables/db. 
postgresdockerlocal-# grant all privileges on database fapidb to postgresdluser;
postgresdockerlocal=# GRANT CONNECT ON DATABASE fapidb TO postgresdluser;
postgresdockerlocal=# GRANT pg_read_all_data TO postgresdluser;
postgresdockerlocal=# GRANT pg_write_all_data TO postgresdluser;
postgresdockerlocal=# GRANT ALL PRIVILEGES ON DATABASE "fapidb" to postgresdluser;
postgresdockerlocal=# GRANT USAGE ON SCHEMA public TO postgresdluser;
postgresdockerlocal=# GRANT ALL ON SCHEMA public TO postgresdluser;
postgresdockerlocal=# GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgresdluser;

## Trying to create a new table from our new user in the database: 
fapidb=# CREATE TABLE tpsqltable(ID INT PRIMARY KEY NOT NULL, NAME TEXT NOT NULL, TYPE TEXT NOT NULL, PHONE INT NOT NULL);
## But above command gave me error - despite debugging different ways, giving all permissions, still error persisted, so I changed my new user to root user - Not a good way to do, but it is what it is... 

postgresdockerlocal=# ALTER DATABASE fapidb OWNER TO postgresdluser; ## as above changes were not working, despite my new user, it was not getting access/privileges, hence changed the db owner
# Hence, if now I have to enter the database bash directly from terminal from updated owner: `psql -U postgresdluser -d fapidb`

postgresdockerlocal=# \c fapidb postgresdluser (to connect to our database with the given user) 
### Note: To connect to database with superuser: postgresdockerlocal=# \c fapidb
fapidb-# \dt (to list down all tables)
fapidb=> SELECT current_user;
fapidb=# CREATE TABLE tpsqltable(ID INT PRIMARY KEY NOT NULL, NAME TEXT NOT NULL, TYPE TEXT NOT NULL, PHONE INT NOT NULL);
fapidb=# INSERT INTO tpsqltable VALUES (1, 'suraj', 'test', 12345);
fapidb=# select * from tpsqltable;
 id | name  | type | phone 
----+-------+------+-------
  1 | suraj | test | 12345
(1 row)

# to get the version or details of the container use: docker inspect postgreslocal (or) podman inspect postgreslocal
We get version is, apart from other details (as I am doing the project): "PG_VERSION=16.2-1.pgdg120+2"
```

![postgres/redis container](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/1postgres%26redis_container_docker.png)

#### **Task2**: Create a logic wherein you can get the health status of your postgres and redis containers from app running on port 8000? 

In database/ dir, I have defined the postgres and redis configs, which I use and later in app.py I check the health of both containers. 

```
I have segregated code in app.py under name Task2 which can be referred. 
Also have created config files in database dir.
Note that in the postgres config defined: Either I can directly use the postgres url defined in variable, or I can export it in my local env by running command in terminal: `export POSTGRES_DB_URL="postgresql://postgresdluser:1234@localhost:7002/fapidb"`
And then extract value from this variable using os.getenv() ~ same can be seen in the postgresDbConfig.py file
```

![postgres status postman](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/6serverhealthypostman.png)
![status when fastapi app is down](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/12servererror.png)

#### **Task3**: Write an async version of health check code for postgres and redis in 8000 port app, and try getting the health status of both sync and async code? 

I have segregated code in app.py file under name Task3 which can be referred. Moving forward the piece of code written to which coresssponding task is well defined in the py files. 
Note: 
- There could be times when app gets stuck or even after refresh it does not send a response or gives ERROR: Address already in use response, in such case, we can kill the app running on port and restart it. Simply put: List the servers using the port using: `lsof -i :8000`.
- Kill the process pid: `kill -9 <pid>`. (Command: `kill <pid>` sends signal (SIGTERM) and tells pid to terminate, but said program can execute some code first or even ignore the signal. `kill -9 <pid>`, on the other hand, forces the program to immediately terminate and cannot be ignored)

![postgres/redis status](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/5serverhealthy.png)

#### **Task4**: Load test the sync and async version of your API using k6, ab (Apache Benchmark), or any other tool? 

First, I have tested using k6. Installing: `brew install k6`. Reading docs, and then put the terminal command: `k6 run loadtest.js`. Configuration used for load testing using k6: 

```
vus: 100,
stages: [
    { duration: '15s', target: 100 }, // ramp up
    { duration: '15s', target: 100 }, // stable
    { duration: '45s', target: 1000 }, // spike - stress test
    { duration: '1m', target: 0 }, // ramp down
  ]
```

Results of k6 load testing: 

```
Results for async code: 
scenarios: (100.00%) 1 scenario, 1000 max VUs, 2m45s max duration (incl. graceful stop):
      * default: Up to 1000 looping VUs for 2m15s over 4 stages (gracefulRampDown: 30s, gracefulStop: 30s)
✗ api status in load test is 200
↳  96% — ✓ 30984 / ✗ 989
checks.........................: 96.90% ✓ 30984      ✗ 989   
data_received..................: 6.7 MB 50 kB/s
data_sent......................: 2.7 MB 20 kB/s
http_req_blocked...............: avg=65.84ms min=0s     med=1µs      max=19.51s p(90)=2µs   p(95)=4µs  
http_req_connecting............: avg=65.83ms min=0s     med=0s       max=19.51s p(90)=0s    p(95)=0s   
http_req_duration..............: avg=1.26s   min=0s     med=823.22ms max=40.57s p(90)=1.78s p(95)=1.97s
{ expected_response:true }...: avg=1.3s    min=6.13ms med=845.72ms max=40.57s p(90)=1.78s p(95)=1.97s
http_req_failed................: 3.09%  ✓ 989        ✗ 30984 
http_req_receiving.............: avg=24.95µs min=0s     med=12µs     max=9.57ms p(90)=37µs  p(95)=58µs 
http_req_sending...............: avg=7.61µs  min=0s     med=4µs      max=3.41ms p(90)=10µs  p(95)=16µs 
http_req_tls_handshaking.......: avg=0s      min=0s     med=0s       max=0s     p(90)=0s    p(95)=0s   
http_req_waiting...............: avg=1.26s   min=0s     med=823.22ms max=40.57s p(90)=1.78s p(95)=1.97s
http_reqs......................: 31973  236.824871/s
iteration_duration.............: avg=2.05s   min=1.68ms med=867.31ms max=54.89s p(90)=1.88s p(95)=2.23s
iterations.....................: 31973  236.824871/s
vus............................: 1      min=1        max=999 
vus_max........................: 1000   min=1000     max=1000
running (2m15.0s), 0000/1000 VUs, 31973 complete and 46 interrupted iterations

Results for sync code: 
scenarios: (100.00%) 1 scenario, 1000 max VUs, 2m45s max duration (incl. graceful stop):
      * default: Up to 1000 looping VUs for 2m15s over 4 stages (gracefulRampDown: 30s, gracefulStop: 30s)
✗ api status in load test is 200
↳  99% — ✓ 17680 / ✗ 29
checks.........................: 99.83% ✓ 17680      ✗ 29    
data_received..................: 3.7 MB 26 kB/s
data_sent......................: 1.5 MB 11 kB/s
http_req_blocked...............: avg=184.17µs min=0s       med=1µs   max=96.35ms p(90)=3µs   p(95)=171µs
http_req_connecting............: avg=179.28µs min=0s       med=0s    max=96.26ms p(90)=0s    p(95)=127µs
http_req_duration..............: avg=3.62s    min=212.27ms med=3.6s  max=33.22s  p(90)=6.35s p(95)=6.7s 
{ expected_response:true }...: avg=3.58s    min=212.27ms med=3.59s max=32.51s  p(90)=6.34s p(95)=6.69s
http_req_failed................: 0.16%  ✓ 29         ✗ 17680 
http_req_receiving.............: avg=35.98µs  min=7µs      med=30µs  max=6.08ms  p(90)=52µs  p(95)=64µs 
http_req_sending...............: avg=11.77µs  min=2µs      med=9µs   max=3.23ms  p(90)=17µs  p(95)=26µs 
http_req_tls_handshaking.......: avg=0s       min=0s       med=0s    max=0s      p(90)=0s    p(95)=0s   
http_req_waiting...............: avg=3.62s    min=212.11ms med=3.6s  max=33.22s  p(90)=6.35s p(95)=6.7s 
http_reqs......................: 17709  125.664217/s
iteration_duration.............: avg=3.62s    min=218.01ms med=3.6s  max=33.22s  p(90)=6.35s p(95)=6.7s 
iterations.....................: 17709  125.664217/s
vus............................: 2      min=2        max=1000
vus_max........................: 1000   min=1000     max=1000
running (2m20.9s), 0000/1000 VUs, 17709 complete and 0 interrupted iterations
```

Observation for async vs sync load testing: `http_req_duration: avg=1.26s vs avg=3.62s`. 
- Note that, 1s response time in itself is also quite huge number, but since we bombarded it with requests, the overall avg is effected; Else it would generally be less than 300ms. 

![k6 async code stress test](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/2async%20code%20stress%20test.png)

Note: After doing stress test on this, my server went down and not responding ~ `http://127.0.0.1:8000/` took too long to respond. Tried restarting app running on port 8000, then postgres/redis containers, still things did not work, so in the end had to kill the processes using `kill -9 <pid>` and then restarted the services using uvicorn. 

Then did the stress testing using ab (Apache benchmark). Read docs/ videos. 
- Simple command eg. that can be used in terminal (no prior setup was needed in my mac, probably it came pre-installed): `ab -k -c 10 -n 50 http://127.0.0.1:8000/asyncrpstatus`. Command means: We will be hitting the endpoint with 10 simultaneous connections until 50 requests are met. It will be done using the keep alive header `-k` used.
- Note: When I increased the connections to a lot say `-c 10000`, got error, since the mac local setup did not allow.

```
Benchmarking 127.0.0.1 (be patient)
socket: Too many open files (24)
```
ab testing for async vs sync
```
async results: 
Command: ab -k -c 350 -n 30000 http://127.0.0.1:8000/asyncrpstatus
Server Software:        uvicorn
Server Hostname:        127.0.0.1
Server Port:            8000
Document Path:          /hasync
Document Length:        91 bytes
Concurrency Level:      100
Time taken for tests:   293.477 seconds
Complete requests:      30000
Failed requests:        0
Keep-Alive requests:    0
Total transferred:      6480000 bytes
HTML transferred:       2730000 bytes
Requests per second:    102.22 [#/sec] (mean)
Time per request:       978.258 [ms] (mean)
Time per request:       9.783 [ms] (mean, across all concurrent requests)
Transfer rate:          21.56 [Kbytes/sec] received
Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.4      0      26
Processing:    31  976 192.8    992    1426
Waiting:       28  967 191.7    982    1416
Total:         35  976 192.8    992    1427
Percentage of the requests served within a certain time (ms)
  50%    992
  66%   1082
  75%   1124
  80%   1146
  90%   1211
  95%   1259
  98%   1302
  99%   1327
 100%   1427 (longest request)

sync results:
Command: ab -k -c 750 -n 30000 http://127.0.0.1:8000/syncrpstatus
Server Software:        uvicorn
Server Hostname:        127.0.0.1
Server Port:            8000
Document Path:          /hsync
Document Length:        85 bytes
Concurrency Level:      100
Time taken for tests:   181.606 seconds
Complete requests:      30000
Failed requests:        0
Keep-Alive requests:    0
Total transferred:      6300000 bytes
HTML transferred:       2550000 bytes
Requests per second:    165.19 [#/sec] (mean)
Time per request:       605.353 [ms] (mean)
Time per request:       6.054 [ms] (mean, across all concurrent requests)
Transfer rate:          33.88 [Kbytes/sec] received
Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    2  46.9      0    1908
Processing:    51  602 149.3    591    2485
Waiting:       47  602 149.3    591    2485
Total:         52  605 156.6    592    2788
Percentage of the requests served within a certain time (ms)
  50%    592
  66%    650
  75%    688
  80%    711
  90%    767
  95%    824
  98%    922
  99%   1038
 100%   2788 (longest request)
```

Observation for async vs sync: 
- `Mean Time per request: 978.258ms vs 605.353`.
- Surprisingly, it showed sync was faster. Again, its probably because the way time per response is spread and not very accurate. p50 to p100 gap: (992 to 1427) vs (592 to 2788) - we observe this is kind of aligned - sync requests did take more time as gap is noticeable. 

Other tools that can be used for testing: jmeter, locust, etc. 

![ab stress test](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/3abStresstest.png)

#### **Task5**: Insert 1M+ records in postgres table and create an endpoint querying some record from the table?

First, I cleaned up the table and refreshed it then inserted records; Steps below; Then added API endpoints to query records as `Task5` heading in comments in the app.py file. 

```
Logged into my fapidb db: postgresdockerlocal=# \c fapidb postgresdluser
fapidb=> truncate tpsqltable;
fapidb=> alter table tpsqltable add address varchar(300);
fapidb=> CREATE TABLE tpsqltable(ID INT PRIMARY KEY NOT NULL, NAME TEXT NOT NULL, TYPE TEXT NOT NULL, PHONE INT NOT NULL);
fapidb=> ALTER TABLE tpsqltable ADD COLUMN created_at TIMESTAMP;
fapidb=> \d+ tpsqltable
                                                    Table "public.tpsqltable"
   Column   |            Type             | Collation | Nullable | Default | Storage  | Compression | Stats target | Description 
------------+-----------------------------+-----------+----------+---------+----------+-------------+--------------+-------------
 id         | integer                     |           | not null |         | plain    |             |              | 
 name       | text                        |           | not null |         | extended |             |              | 
 type       | text                        |           | not null |         | extended |             |              | 
 phone      | integer                     |           | not null |         | plain    |             |              | 
 address    | character varying(300)      |           |          |         | extended |             |              | 
 created_at | timestamp without time zone |           |          |         | plain    |             |              | 
Indexes:
    "tpsqltable_pkey" PRIMARY KEY, btree (id)
Access method: heap
fapidb=> alter table tpsqltable alter column phone type bigint;
Now, time to insert 1M records; Script to run in db container terminal: 
Query: 
INSERT INTO tpsqltable (id, name, type, phone, address, created_at)
SELECT s AS id, 'name_' || s AS name,
CASE WHEN s % 3 = 0 THEN 'type1'
     WHEN s % 3 = 1 THEN 'type2'
     ELSE 'type3'
END AS type,
(CASE WHEN random() < 0.5 THEN 8000000000 ELSE 9000000000 END + s % 1000000) AS phone,
'address data ' || s AS address,
'2000-01-01'::timestamp + (s % 3650 || ' days')::interval AS created_at
FROM generate_series(1, 5000000) AS s;

Now, shuffling all the records:
-- Step 1: Create a new table with shuffled rows: CREATE TABLE shuffled_table AS SELECT * FROM tpsqltable ORDER BY random();
-- Step 2: Drop the original table: DROP TABLE tpsqltable;
-- Step 3: Rename the shuffled table to the original table name: ALTER TABLE shuffled_table RENAME TO tpsqltable;

To understand query details we can use 'explain' keyword in pgsql. 
Eg: 
------------------------------------------------------------------------------
fapidb=> explain select * from tpsqltable where phone=9000516507;
 Gather  (cost=1000.00..83875.96 rows=3 width=66)
   Workers Planned: 2
   ->  Parallel Seq Scan on tpsqltable  (cost=0.00..82875.66 rows=1 width=66)
         Filter: (phone = '9000516507'::bigint)
(4 rows)
------------------------------------------------------------------------------
fapidb=> explain select * from tpsqltable;
 Seq Scan on tpsqltable  (cost=0.00..106835.82 rows=5000382 width=66)
(1 row)
------------------------------------------------------------------------------
fapidb=> explain select * from tpsqltable order by created_at;
 Gather Merge  (cost=468247.39..954429.47 rows=4166984 width=66)
   Workers Planned: 2
   ->  Sort  (cost=467247.37..472456.10 rows=2083492 width=66)
         Sort Key: created_at
         ->  Parallel Seq Scan on tpsqltable  (cost=0.00..77666.93 rows=2083492 width=66)
(5 rows)
------------------------------------------------------------------------------
```

![fetching records from postgres table via API](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/7serverhealthy.png)

#### **Task6**: Dockerize/Containerize the businessMicroservice?

- I have created a dockerfile for the repo, and now building the current service using: `podman build --no-cache -t bmserviceimage .` (Note that `.` indicates current dir; Else syntax would be (docker/podman): `docker build -t <image> <path>`).
- Once image was build, I ran the image, i.e spawn up the container with a name using: `podman run -p 4500:8900 --name bmservicecontainer bmserviceimage`. In short, it is port mapping to our fastapi server running inside the container. Then we can hit APIs via Postman/Browser and see response. Our postgres and redis cotainers are anyways running from previous commands.
- I have added explicit details inside the Dockerfile. Also, note, if there is a code change made, then image must be rebuilt. To run the container in some other port parallely using same image, simply: `podman run -p 4600:8900 --name bmservicecontainer bmserviceimage`

![building docker image](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/8buildingdockerimage.png)
![bmservice container logs](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/10dockercontainerlogs.png)
![bmservice container folder dir as defined in our dockerfile](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/11dockercontainerterminal-file_directory.png)
![env variables inside bmservice container](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/13dockercontainerterminalenvvariables.png)

#### **Task7**: Since businessMicroservice is dockerized try connecting to the other Redis/Postgres containers - for now we can say it is loosely coupled?

The only thing changed is the host machine in the redis/postgres configs. Now what changed?: 
- When I did not dockerize my fastapi app and ran it on localhost (means it basically ran on my macbook/host machine) and hit postgres or redis container for health check - I got a response. Understand that postgres and redis containers were also running on host machine only. Hence all shared the same network namespace. This means that localhost referred to the same machine for both the FastAPI application and PostgreSQL/Redis.
- So credentials like: POSTGRES_HOST/REDIS_HOST = "localhost". When I dockerized my fastapi app and ran it in a docker container the networking context changed. Key points:
- Isolation: Each Docker container has its own network stack. localhost within a Docker container refers to the container itself, not the host machine.
- Networking: By default, Docker containers are attached to a default network (bridge network) which isolates them from the host network and from each other unless configured otherwise.
- By default, Docker containers are connected to a bridge network. To allow your FastAPI container to communicate with PostgreSQL/Redis running on the host machine, you should use the host machine's IP address. So its like host machine is a common ground/platform for multiple containers running inside it, so any request should be routed via the machine so that it can exactly know which container is interacting with which one - in a rough explanation.
- You can find host machine (in my case macbook) ip using `ping -c 1 $(hostname)` or `ifconfig` command; If it were an AWS EC2 machine, we would anyways know the IP of the machine...; Then update your FastAPI configuration to use this IP address (host machine) instead of localhost i.e update POSTGRES_HOST url, which I did in code in postgresDbConfig.py.
- Note: The IP addresses are given to us by an Internet Service Provider (ISP). You will be able to connect your computer and modem to their network and access the Internet after the ISP visits your home to install your connection. When you launch a Web browser to conduct a Google search or send an email, and everything goes smoothly, you can be sure that everything is functioning as it should. If it initially doesn't work, you might need to engage with your ISP's technical support team to have things resolved. When you establish a new connection, one of the initial things you could do is to check your IP address. Please take note of the IP address, but avoid becoming overly attached because it's possible that your ISP uses a dynamic IP address, that means it could change without warning. To have a static IP you have to tell your ISP provider. But why dynamic IP?: It is solely a numerical issue. There are a countless number of computer users connected to the Internet simultaneously all over the world. Some people use the Internet frequently, while others only occasionally, and occasionally only long enough to write an email. Every person who is available on the internet needs a distinct IP address, as was already mentioned. When you consider all the logistics involved, it would have been extremely costly to assign a fixed, static IP to each and every ISP subscriber. Additionally, the number of static IP addresses might have quickly run out with the current IP address generation (basically IPv4).Dynamic IP addresses were subsequently introduced to the world of the Internet. This made it possible for ISPs to give their customers a dynamic IP address as needed. Every time you go online, that IP address is essentially "loaned" to you. [Reference](https://www.javatpoint.com/why-has-my-ip-address-changed).
- Hence, you may also observe a change in your macbook/host IP if you switch from wifi to mobile hotspot for your macbook internet connectivity. (In following tasks, your host IP will play an important role in connecting the microservices, hence keep note of this point)
- We can ask how is docker able to route the connection from container to host machine via bridge network concept?:
  - Bridge Network Creation: By default, Docker containers are connected to a bridge network. This is an internal virtual network that allows containers to communicate with each other and the host machine.
  - Container-to-Host Communication: When you specify the host machine's IP address in the container, the container's networking stack knows to route the traffic out of the container to the host machine's network interface.
  - Network Address Translation (NAT): Docker uses Network Address Translation to map container ports to host ports. When a container tries to access an IP address and port, Docker's networking translates these into appropriate network requests.
  - To access a service running on the host machine from a Docker container, you specify the host machine's IP address. For example, if your host machine's IP address is 192.168.1.100, you can configure your application to connect to this IP.

![all running docker containers on local](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/9allimages.png)

#### **Task8**: Use docker compose and integrate all 3 services (fastapi app, postgres, redis) and tighten up the coupling? 

- A Docker Compose file, typically named docker-compose.yml, is used to define and manage multi-container Docker applications. It allows you to define services, networks, and volumes in a single YAML file, providing a streamlined way to manage your Docker environment. (More details added in docker-compose.yaml file in the project)
- Can check the docker-compose.yaml file for reference. Do ensure docker/podman compose utilities are installed as they need to be installed seaprately and do not come packed with usual docker/podman.
- To build the compose file: `docker-compose build` (or `podman-compose build`). Note you can remove `-` and run command as well like: `podman compose build`.
- To run it: `docker-compose up` (or `podman-compose up`); To run in detached mode add `-d` flag.
- Then you can access the service on from browser/postman. You may also use: `docker-compose up --build` (or `podman-compose up --build`)
- To stop and remove containers created by docker-compose up, use Ctrl+C in the terminal where it's running or use: `docker-compose down`. If you add `-v` flag in docker-compose down it will remove the volumes as well apart from stopping containers.
- Note that in docker file I have made the CMD command to run both app.py fastapi server as well as main.py fastapi server. Though we won't be able to get the status in the usual way from app.py to main.py; Same is objective in next task.
- To run an individual component of docker compose (docker/podman): `podman-compose up <service_name>`
- To enter into the container bash/terminal from compose (docker/podman): `podman-compose exec postgreslocalservice bash`

![docker compose containers](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/14dockercomposecontainers.png)
![redis status from fastapi app running via compose](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/15serverhealthy.png)
![get into the container terminals of a service running via compose (docker/podman)](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/31podman%20compose%20exec%20bash.png)
![view docker volume attached to a container in compose](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/35view_docker_volumes_in_a_container.png)

#### **Task9**: Ensure you are able to get status of main.py server in sampleService from app.py service from the docker-compose file?

If we see the current way in which we get status of main app server is: 

```
@app.get("/mainappstatus")
def get_other_server_status():
    url = 'http://127.0.0.1:8001/currentStatus' # Note that endpoint is camelCase, same is expected when typing in url/testing via postman
    response = requests.get(url)
    print(f"Status of main app server: {response.status_code}")
    data = json.loads(response.text)
    return data
```
But now, since we are considering spinning up the multiple fastapi servers inside the container - to be able to access them from our host machine (i.e macbook) - we need to be able to map a host machine port to that service port, and then anyways we are aware of the concept of docker bridge network, etc., it will be able to get the status. Changes to do the same have been made in the docker compose file. 

To explain in other way: 

- In Docker Compose, the ports directive is used to map ports from the host machine to the container. This allows services running inside the container to be accessible from the host machine.
- Mapping ports is essential because containers are isolated environments, and by default, the services running inside them are not accessible from the outside world. By mapping a container's port to a port on the host machine, you make the service inside the container accessible from outside the container, using the host's IP address and the mapped port.
- If we observe current docker-compose file: "4500:8900"; This maps port 8900 inside the container to port 4500 on the host machine. It means that if you access `http://localhost:4500` from browser/postman on your host machine, it will be directed to the service running on port 8900 inside the container.
- Then - Change that we made: "4501:8901": This maps port 8901 inside the container to port 4501 on the host machine. It means that if you access `http://localhost:4501` from browser/postman on your host machine, it will be directed to the service running on port 8901 inside the container.
- If you have two FastAPI applications running on different ports (8900 and 8901) inside the same container, you need to map both ports to the host machine to access them: Primary FastAPI Application: Internal port: 8900, Mapped host port: 4500, Access via: `http://localhost:4500`
- For this: Secondary FastAPI Application: Internal port: 8901, Mapped host port: 4501, Access via: `http://localhost:4501`
- This is the case when we are accessing them from our browser/postman.
- But now, if I want to check the health of main.py server from app.py server - remember both of them are running in the same container environment - so the request in code will be from one port to another inside the container itself not on host machine.
- This is an inter-service communication - for this we leverage docker (or podman) compose’s internal DNS resolution, allowing one service to communicate with another by using its service name.
- Hence the url we hit to changed to: `url = 'http://businessmicroservice:8901/currentmainstatusdockercompose'`
- To reiterate simply, to access main.py app server - there are 2 ways:
  - One, we type-in the url from our browser/postman (which is host machine) and access the main.py server running inside container - which we did by port mapping 4501:8901.
  - Two, we type-in url to access app.py server running inside container since it is already exposed. And then we define an endpoint inside app.py server which internally communicates with main.py server - which is what we did in this particular url case: `url = 'http://businessmicroservice:8901/currentmainstatusdockercompose'`. With `businessmicroservice:8901`, we ensured our app.py server is able to access main.py server inside container. Else, we get `ERROR: requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8901): Max retries exceeded with url`

#### **Task10**: Build a simple consumerMicroservice app pinging root server of businessMicroservice? 

Wrote Dockerfile of the consumerMicroservice and fastapi code to ping to businessMicroservice app. Also ensured by venv is activated. Since consumerMicroservice is a separate service altogether I am spinning it up manually from Docker. Docker compose is not needed as its just 1 service. From docker compose anyways I have spinned up businessMicroservice app/ postgres/ redis.

Command used (docker/podman): `podman build --no-cache -t cmserviceimage .`

Once image was build, to run container (THERE IS A CAVEAT HERE - SO KEEP FOLLOWING; DETAILS EXPLAINED ON THIS BELOW): `podman run -p 3500:6800 --name cmservicecontainer cmserviceimage` - Connecting host's 3500 port with 6800 port of container (Note check Dockerfile - I am exposing port 6800 of container where the consumer service fastapi server is running using uvicorn)

In app.py code of both consumer & business microservice, see the url is connecting to the fast api server running in another container; Though understand that both containers are running in same host machine (my macbook). 

Recall that: A network is a group of two or more devices that can communicate with each other either physically or virtually. The Docker network is a virtual network created by Docker to enable communication between Docker containers. If two containers are running on the same host they can communicate with each other without the need for ports to be exposed to the host machine.

In our case, we put our docker compose containers from businessMicroservice in a network named: `bmservice_compose_network`

We use this and connect our consumerMicroservice which is an external container. 
In businessMicroservice: Defined `/bmserviceserverstatus` to return response when we hit a service running in another container; url we are hitting: `http://businessmicroservice:8901/bmserviceserverstatus` - Recall we are running the app server using docker compose at port 8901 in businessMicroservice, for run via normal docker (without compose) or from host we use different  ports as seen in earlier tasks, but for testing current task we have activated this port by keeping the service up using docker compose and it is running in network: `bmservice_compose_network`. 

In consumerMicroservce: From host machine I hit `/bmservicestatus` endpoint to get `/bmserviceserverstatus` defined in businessMicroservice; RECALL THE CAVEAT HIGHLIGHTED EARLIER: Upon running earlier command: `podman run -p 3500:6800 --name cmservicecontainer cmserviceimage` and hitting `http://0.0.0.0:3500/bmservicestatus` on browser/postman did not yield me any response from other container. Why?: It was because the containers running via compose are on a different network. Hence I need to connect the container to that network; It can be done by running (docker/podman): `podman run --network bmservice_compose_network -p 3500:6800 --name cmservicecontainer cmserviceimage` - network added. (Note rebuild image and then run, also ensure the directory you are building your dockerfile and all - don't mess up here)

Note that - we can also imagine coupling the consumerMicroservice inside the same docker-compose file as well specifying the path (build context as something like `./consumerMicroservice` than giving `.`) and have all services - businessMicroservice, postgres, redis, etc running up altogether. But we are restricting now as a fundamental understanding has been developed by this far and we can try avoiding cluttering things more... 

![all running docker networks in local](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/18dockernetworklist.png)
![response we hit health check api of consumerMicroservice app](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/17serverhealth.png)
![response when consumerMicroservice app hits businessMicroservice app health check api](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/19serverhealth.png)

#### **Task11**: Publish the docker-compose file having businessMicroservice, postgres, redis to dockerhub and check if another developer can pull the image and run it on their machine?

Commands ran: 
- When in dir: `/consumerMicroservice`: ` podman build --no-cache -t frpconsumermicroservicedockersrj .`
- When in dir: `/businessMicroservice`: `podman compose build` and `podman build --no-cache -t frpbusinessmicroservicedockersrj .`
- To push `frpconsumermicroservicedockersrj`:

```
podman login -u surajv311 -p <my_password>  docker.io/surajv311/frpconsumermicroservicedockersrj
podman images  (to select the image_id and run below command)
podman push 8caafac0cb3c docker://docker.io/surajv311/frpconsumermicroservicedockersrj:1.0.0  
```

Link: https://hub.docker.com/r/surajv311/frpconsumermicroservicedockersrj

To push `frpbusinessmicroservicedockersrj`:

```
podman login -u surajv311 -p <my_password>  docker.io/surajv311/frpbusinessmicroservicedockersrj
podman images  (to select the image_id and run below command)
podman push 23ed0e8617b5 docker://docker.io/surajv311/frpbusinessmicroservicedockersrj:1.0.0
```

Link: https://hub.docker.com/r/surajv311/frpbusinessmicroservicedockersrj

As a sidenote, if we see, our postgres container is named `postgreslocalservice-1` in Docker desktop/Podman, though in our docker compose file we have named container as `container_name: postgreslocalcontainer`. (Discussed before): 
- To get into container bash, use the defined name only, i.e: (docker/podman) `podman exec -it postgreslocalcontainer bash`
- To get into the db inside container: `psql -U postgresdluser -d fapidb`
- Table query: `fapidb=# select * from tpsqltable limit 10;`

#### **Task12**: Build CRUD operations in databases (postgres, redis) logic in businessMicroserviceApp and expose the endpoints to consumerMicroserviceApp. Hence use consumerMicroserviceApp to alter the data using businessMicroserviceApp as intermediary. 

Task complete, we can check the corresponding app.py, config and schema files. Let us revisit the flow of the way project is developed: 

**First**: 
- We ran our fastapi servers inside host machine at ports 8000 and 8001 using commands: `uvicorn app:app --port 8000 --reload`

**Second**: 
- We spawn up Redis and Postgres docker containers on same host machine using commands like (docker/podman): `docker run --name redislocal -p 7001:6379 redis`, `docker run --name postgreslocal -p 7002:5432  -e POSTGRES_PASSWORD=1234 -e POSTGRES_USER=postgresdockerlocal postgres`.
- Understand we can access them from port 7001/7002 of host machine, but if we hit directly - we won't get response as it's a database server, not web server. The postgres url we hit from fastapi server running on port 8000: `POSTGRES_DB_URL=postgresql://postgresdluser:1234@localhost:7002/fapidb`. Observe the host address: `localhost:7002`

**Third**:
- Tested async-sync versions of code, load tested APIs, populated postgres table with 1M+ rows, etc. 

**Fourth**: 
- Containerized the fastapi server. So now, instead of it running on host, it will run a level below the surface which is a container. 
- Created Dockerfile for the fastapi app. Exposed a port with which I can communicate from host/browser/postman to the server running inside the container (port mapping).
- Also, explicitly update Dockerfile for the container to except request from outside interface by adding a flag in uvicorn command: `--host 0.0.0.0`
- Commands (docker/podman): `podman build --no-cache -t bmserviceimage .`, `podman run -p 4500:8900 --name bmservicecontainer bmserviceimage`

**Fifth**: 
- Ensure my dockerized fastapi app server running inside container can interact with other postgres/redis containers. 
- Understand that now the command ground is the host - having 3 running containers which have to interact with eachother. Earlier, our fastapi app was running on browser/host itself which is kind of on the surface than a level beneath i.e container. 
- We had to ensure that now Redis/Postgres hosts are also updated - so postgres db url became: `POSTGRES_DB_URL=postgresql://postgresdluser:1234@192.168.29.72:7002/fapidb`. Observe we switched from localhost to host IP: `192.168.29.72`. So port `7002` exposed of the machine to enter the microservice/container.  
- Now the flow is like to check the db status/health: I hit a url in my browser/host/postman with host 4500/<api>. This 4500 port is mapped to a port inside container where my fastapi server is running - so the request travels to port 8900 (port mapping) inside container. Now the container wouldn't directly allow any request from any entity, hence recall we had whitelisted requests by specifically adding `-host 0.0.0.0` keyword in uvicorn fastapi app when it is spawn up in Dockerfile (Note this is the default host that needs to be added - I tried making host as 127.0.0.1 or a different one, but that doesn't work - so basically this is the only host port which is allowed so when I hit api from my browser or postman - I do not hit 127.0.0.1/<api> or localhost/<api>, rather 0.0.0.0/<api> - as this is whitelisted). So container allows request from host to hit the server. Now, fastapi server has an API endpoint say: `syncphealth` to check postgres health. When I hit this API from 0.0.0.0/<syncphealth>; if you check the code, upon hitting the api it initiates a postgres db session from SessionLocal(). Inside SessionLocal() code, another switch happens which was the host port is changed from localhost to machine ip address (check previous point), thereby brining our service on common ground which is the host machine. Docker handles this internally using NAT, Docker bridge, etc, and hence our fastapi server running inside a container is able to hit the postgres container running on host - as url is updated to leverage host machine address. Similar, case for redis. 

**Sixth**:
- Exposed/ spawn up another service inside same container running on port: `4501:8901`. So 8900 service interacted with 8901 service. 

**Seventh**:
- Docker composed fastapi container (businessMicroservice), postgres container, redis container in the same network named `bmservice_network`. 
- Later created another microservice (consumerMicroservice mapped from `3500:6800` host-container service port mapping) but it could not directly hit the fastapi/postgres/redis containers as they were a part of a network. 
- I had to spawn up the consumerMicroservice in same network using (docker/podman): `podman run --network bmservice_compose_network -p 3500:6800 --name cmservicecontainer cmserviceimage` and was able to hit the APIs.

![all docker compose services now](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/24all_dockercompose_services.png)
![how to hit a post request in postman](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/30postgresCRUD_postapi_request_body_options_postman.png)
![hitting postgres db to fetch records from API if there are no records - error pic](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/16serverhealth-postgres-but-no-data-in-table-data-not-persisted.png)
![postgres crud - get api response](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/20postgresCRUD_getapi.png)
![postgres crud - put api response](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/21postgresCRUD_putapi.png)
![postgres crud - delete api response](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/22postgresCRUD_deleteapi.png)
![postgres crud - post api response](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/23postgresCRUD_postdeletegetapi.png)
![validating CRUD operations data inside postgres container](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/29checking_inside_postgres_container_after_POST_api_call_from_code.png)
![hitting businessMicroservice app apis from consumerMicroservice app eg 1](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/25crudapisexample.png)
![hitting businessMicroservice app apis from consumerMicroservice app eg 2](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/27consumerMicroservice_hitting_businessMicroserviceAPI_get_postgres_data.png)
![pydantic response validation error if our api response is not inline with defined schema eg 1](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/26_pydantic_response_validation_error_ref.png)
![pydantic response validation error if our api response is not inline with defined schema eg 2](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/28missing_field_validation.png)
![redis crud - get api response](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/32redisCRUD_getapi.png)
![redis crud - post api response](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/33redisCRUD_postapi.png)
![validating CRUD operations data inside redis container](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/34checking_inside_redis_container_after_POST_api_call_from_code.png)

#### **Task13**: Run the businessMicroservice in 2 instances. And your consumerMicroservice app should be pinging root server of the different isntances of businessMicroservice app in round-robin fashion; In case it the service dies in one port, then redirect all request to other port - similar to how a simple load balancer would work? 

A rough overview of how our ports and services are mapped until now in docker compose: 
![overview of services until now](https://github.com/surajvm1/LearningMicroservices/blob/dev/feat1/snapshot_references/Fapi_project.drawio.png)

Now,...(WIP)
For ref later: https://www.reddit.com/r/docker/comments/mje7u2/dockercompose_dynamically_static_port_assignments/
Dynamically do port mapping for multiple services? Is it possible? 
gpt says: To run two instances of the businessmicroservice service in Docker using docker-compose, you can use a feature called "replicas" which is available in Docker Compose version 3.4 and higher. However, to ensure each instance maps to a different port on the host, you will need to define separate services for each instance, as Docker Compose does not support dynamic port mapping for replicated services.
But will reddit link help? 

#### **Task14**: Setup another NoSQL db like mongodb via docker and health check mongodb service?  

#### **Task15**: Setup Kafka manually or via docker on local. Create JSON events from a service and publish it to Kafka service?

#### **Task16**: Add API test cases in the project? 

#### **Task17**: Add poetry to lock the packages?

- For later reference??: https://www.geeksforgeeks.org/how-to-add-python-poetry-to-an-existing-project/
- https://realpython.com/dependency-management-python-poetry/

------------------------------------

#### Bugs found: 

- Even after adding volumes in docker compose file for postgres/redis. It has been observed that if I restart/terminate-start the containers; the data is not persisted. Fix it.
- In dockerfile for businessMicroservice to start fastapi server - either I could define and trigger the uvicorn command from dockerfile, or define the command in a `sh` file and then trigger it; In second approach when I trigger it from sh file, I get error. Fix it. (Error: `preparing container for attach: crun: open executable: Permission denied: OCI permission denied`)

------------------------------------

#### Other learnings: 

Apart from the info I've written in the tasks in readme, or the comments I have added in code, some other things learned:
- What is the difference between 0.0.0.0, 127.0.0.1 and localhost?: https://stackoverflow.com/questions/20778771/what-is-the-difference-between-0-0-0-0-127-0-0-1-and-localhost
- Pydantic is the most widely used data validation library for Python. 
- In Python, a data class is a class that is designed to only hold data values. They aren't different from regular classes, but they usually don't have any other methods. They are typically used to store information that will be passed between different parts of a program or a system: https://www.dataquest.io/blog/how-to-use-python-data-classes/
- A class defined inside another class is known as an inner class in Python. Sometimes inner class is also called nested class. If the inner class is instantiated, the object of inner class can also be used by the parent class. Object of inner class becomes one of the attributes of the outer class. Inner class automatically inherits the attributes of the outer class without formally establishing inheritance.
- Redis-Fastapi-Postgres: 
  - Postgres database in Docker: https://www.commandprompt.com/education/how-to-create-a-postgresql-database-in-docker/
  - Spin up Redis on Docker and learn basic commands: https://www.youtube.com/watch?v=ZkwKyUZWkp4
  - FastAPI Redis Tutorial: https://www.youtube.com/watch?v=reNPNDustQU
  - Fastapi RESTful API CRUD postgresql: https://www.youtube.com/watch?v=d_ugoWsvGLI
  - FastAPI with PostgreSQL and Docker: https://www.youtube.com/watch?v=2X8B_X2c27Q
  - A Guide to Connecting PostgreSQL and Pythons' Fast API: From Installation to Integration: https://medium.com/@kevinkoech265/a-guide-to-connecting-postgresql-and-pythons-fast-api-from-installation-to-integration-825f875f9f7d
  - How to Integrate FastAPI with PostgreSQL: https://www.squash.io/connecting-fastapi-with-postgresql-a-practical-approach/
  - 0.0.0.0 instead of localhost for port: https://www.reddit.com/r/docker/comments/rk1kfp/0000_instead_of_localhost_for_port/
  - Fastapi background tasks, startup events: 
    - https://fastapi.tiangolo.com/tutorial/background-tasks/
    - https://fastapi.tiangolo.com/advanced/events/#startup-event
- CGI (Common Gateway interfaces), WSGI, ASGI: Common Gateway Interface (CGI) is an interface specification that enables web servers to execute an external program to process HTTP or HTTPS user requests. Uvicorn is a web server. It handles network communication - receiving requests from client applications such as users' browsers and sending responses to them. It communicates with FastAPI using the Asynchronous Server Gateway Interface (ASGI), a standard API for Python web servers that run asynchronous code. When a user enters a web site, their browser makes a connection to the site’s web server (this is called the request). The server looks up the file in the file system and sends it back to the user’s browser, which displays it (this is the response). This is roughly how the underlying protocol, HTTP, works. Dynamic web sites are not based on files in the file system, but rather on programs which are run by the web server when a request comes in, and which generate the content that is returned to the user. They can do all sorts of useful things, like display the postings of a bulletin board, show your email, configure software, or just display the current time. These programs can be written in any programming language the server supports. Since most servers support Python, it is easy to use Python to create dynamic web sites. Most HTTP servers are written in C or C++, so they cannot execute Python code directly – a bridge is needed between the server and the program. These bridges, or rather interfaces, define how programs interact with the server. There have been numerous attempts to create the best possible interface, but there are only a few worth mentioning. Not every web server supports every interface. Many web servers only support old, now-obsolete interfaces; however, they can often be extended using third-party modules to support newer ones. This interface, most commonly referred to as “CGI”, is the oldest, and is supported by nearly every web server out of the box. Programs using CGI to communicate with their web server need to be started by the server for every request. So, every request starts a new Python interpreter – which takes some time to start up – thus making the whole interface only usable for low load situations. The upside of CGI is that it is simple – writing a Python program which uses CGI is a matter of about three lines of code. This simplicity comes at a price: it does very few things to help the developer. Using CGI sometimes leads to small annoyances while trying to get these scripts to run. The Web Server Gateway Interface, or WSGI for short, is defined in PEP 333 and is currently the best way to do Python web programming. While it is great for programmers writing frameworks, a normal web developer does not need to get in direct contact with it. When choosing a framework for web development it is a good idea to choose one which supports WSGI. The big benefit of WSGI is the unification of the application programming interface. When your program is compatible with WSGI – which at the outer level means that the framework you are using has support for WSGI – your program can be deployed via any web server interface for which there are WSGI wrappers. You do not need to care about whether the application user uses mod_python or FastCGI or mod_wsgi – with WSGI your application will work on any gateway interface. The Python standard library contains its own WSGI server, wsgiref, which is a small web server that can be used for testing. Another definition: A WSGI server, which stands for Web Server Gateway Interface, is a specification that allows web servers to communicate with Python web applications. It acts as a middleman between the web server (like Nginx or Apache) and the web application written in Python.
  - https://en.wikipedia.org/wiki/Common_Gateway_Interface
  - https://docs.python.org/2/howto/webservers.html
  - https://www.fullstackpython.com/wsgi-servers.html
  - (and chatgpt...for info)
- Postgres db: 
  - Postgres docker image in dockerhub: https://hub.docker.com/_/postgres
  - dbeaver can be used to view postgres db UI. 
  - User permissions/ db accesses: 
    - https://stackoverflow.com/questions/22483555/postgresql-give-all-permissions-to-a-user-on-a-postgresql-database
    - https://stackoverflow.com/questions/50180667/how-can-i-connect-to-a-database-as-another-user
    - https://stackoverflow.com/questions/60138692/sqlalchemy-psycopg2-errors-insufficientprivilege-permission-denied-for-relation
    - https://stackoverflow.com/questions/63044935/flask-sqlalchemy-postgres-error-could-not-connect-to-server-connection-refuse
  - Insert 1M records postgres: https://stackoverflow.com/questions/59169855/inserting-1-million-random-data-into-postgresql
  - ORDER BY random in postgres: https://dba.stackexchange.com/questions/261549/order-by-random-meaning-postgresql
  - Postgres Explain Explained - How Databases Prepare Optimal Query Plans to Execute SQL: https://www.youtube.com/watch?v=P7EUFtjeAmI
- Load testing k6/ab: 
  - k6, tweak OS limits for load testing (NOT RECOMMENDED): https://grafana.com/docs/k6/latest/set-up/fine-tune-os/
  - ab load testing: 
    - https://stackoverflow.com/questions/12732182/ab-load-testing
    - https://www.youtube.com/watch?v=gvounvDSDGg
- Series & Parallel asyncio calls: https://gist.github.com/vinayaksuresh/c1b6eeb09f71cb6df980d4fc9e425989
- Docker: 
  - Tutorial: 
    - Part1: https://www.youtube.com/watch?v=fSmLiOMp2qI
    - Part2: https://www.youtube.com/watch?v=KuCwrySinqI
  - The sequence in which you execute instructions in Dockerfile matters a lot: https://docs.docker.com/build/cache/
  - Push docker image using podman: https://stackoverflow.com/questions/64199116/how-to-push-an-image-to-the-docker-registry-using-podman
  - 'docker-compose' creating multiple instances for the same image: https://stackoverflow.com/questions/39663096/docker-compose-creating-multiple-instances-for-the-same-image
  - What exactly is 'Building'?: Building means many things to many people, but in general it means starting with source files produced by developers and ending with things like installation packages that are ready for deployment; 
    - https://stackoverflow.com/questions/1622506/what-exactly-is-building
  - Multi-stage builds are useful to anyone who has struggled to optimize Dockerfiles while keeping them easy to read and maintain. With multi-stage builds, you use multiple FROM statements in your Dockerfile. Each FROM instruction can use a different base, and each of them begins a new stage of the build. You can selectively copy artifacts from one stage to another, leaving behind everything you don't want in the final image; 
    - https://docs.docker.com/build/building/multi-stage/
  - Difference between the 'COPY' and 'ADD' commands in a Dockerfile?: COPY is same as 'ADD', but without the tar and remote URL handling. In other words, they work similarly, just that ADD can do more things;
    - https://stackoverflow.com/questions/24958140/what-is-the-difference-between-the-copy-and-add-commands-in-a-dockerfile
  - Difference between CMD and ENTRYPOINT in a Dockerfile?: The ENTRYPOINT specifies a command that will always be executed when the container starts. The CMD specifies arguments that will be fed to the ENTRYPOINT; 
    - https://stackoverflow.com/questions/21553353/what-is-the-difference-between-cmd-and-entrypoint-in-a-dockerfile
  - Docker containers internals: https://github.com/surajvm1/demystifying-containers/blob/master/part1-kernel-space/post.md
  - Run games using docker?: https://www.reddit.com/r/docker/comments/1763y1q/run_games_using_docker/
  - What are the differences between ubuntu and an ubuntu docker image, or something similar?: 
    - https://stackoverflow.com/questions/50551846/what-are-the-differences-between-ubuntu-and-and-an-ubuntu-docker-image
    - https://stackoverflow.com/questions/20274162/why-do-you-need-a-base-image-with-docker
    - Do all docker images have minimal OS?: https://stackoverflow.com/questions/46708721/do-all-docker-images-have-minimal-os
  - Difference between "docker compose" and "docker-compose": https://stackoverflow.com/questions/66514436/difference-between-docker-compose-and-docker-compose
  - Where are docker images stored physically on macos?: https://stackoverflow.com/questions/54148999/where-are-docker-images-stored-physically-on-macos
  - Docker bridge network: https://medium.com/@augustineozor/understanding-docker-bridge-network-6e499da50f65
- AWS Dynamodb architecture paper: https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf


------------------------------------

