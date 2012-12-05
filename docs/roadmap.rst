=======
Roadmap
=======

Release 1
=========

yay3

Class to interface with a RESTful API and a Minimal POC in TastyPie so configuration databases are supported

minimal cluster to support push API for a single dedicated server

Parts
-----

State
~~~~~

Amazon: S3
Dedicated: Files
Others: Files on Brightbox

Compute
~~~~~~~

Amazon: EC2
Dedicated: Computers
Others: Brightbox, Fedora Cobbler

LoadBalancer
~~~~~~~~~~~~

Amazon: ELB
Dedicated: HAProxy
Others: Brightbox load balancing service

DNS
~~~

Amazon: Route 53
Dedicated: BIND
Others: GANDI

Bucket Storage
~~~~~~~~~~~~~~

Amazon: S3
Dedicated: Files?
Others: Nimbus.io

RDBMS
~~~~~

Amazon: RDS
Dedicated: Postgres
Others: Heroku? Postgres on Brightbox




Release 2
=========

2 Cloudfront
2 Elasticache
2 SQS
2 EBS

Release 3
=========

3 Cloudwatch
3 Elastic beanstalk
3 Cloudsearch
3 Autoscaling
