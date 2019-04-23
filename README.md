# BUPT EE Experiment, 2019 Spring

![Demo](https://github.com/Vito-Swift/BUPT-EE-2019Exp/assets/show.png)

Environment: Ubuntu 18.04

Database Version: MySQL 2.5.25 ubuntu

---

## How to Start

Fetch the complete source code to local
```
git clone https://github.com/Vito-Swift/BUPT-EE-2019Exp.git
```


## Pre-Configuration

### MySQL Preparation

#### Install MySQL on Ubuntu

```
$ sudo apt update
$ sudo apt install mysql-server
```

#### Configure MySQL

```
$ sudo mysql_secure_installation

Securing the MySQL server deployment.

Connecting to MySQL using a blank password.

VALIDATE PASSWORD PLUGIN can be used to test passwords
and improve security. It checks the strength of password
and allows the users to set only those passwords which are
secure enough. Would you like to setup VALIDATE PASSWORD plugin?

Press y|Y for Yes, any other key for No: N
Please set the password for root here.

New password: 

Re-enter new password: 
By default, a MySQL installation has an anonymous user,
allowing anyone to log into MySQL without having to have
a user account created for them. This is intended only for
testing, and to make the installation go a bit smoother.
You should remove them before moving into a production
environment.

Remove anonymous users? (Press y|Y for Yes, any other key for No) :   

 ... skipping.


Normally, root should only be allowed to connect from
'localhost'. This ensures that someone cannot guess at
the root password from the network.

Disallow root login remotely? (Press y|Y for Yes, any other key for No) : Y  
Success.

By default, MySQL comes with a database named 'test' that
anyone can access. This is also intended only for testing,
and should be removed before moving into a production
environment.


Remove test database and access to it? (Press y|Y for Yes, any other key for No) : 

 ... skipping.
Reloading the privilege tables will ensure that all changes
made so far will take effect immediately.

Reload privilege tables now? (Press y|Y for Yes, any other key for No) : Y
Success.

All done! 
```

#### Initialize MySQL

First we need to adjust user authentication and privileges in case no passwd login can be allowed initially.

```
$ sudo mysql
mysql> SELECT user,authentication_string,plugin,host FROM mysql.user;
+------------------+-------------------------------------------+-----------------------+-----------+
| user             | authentication_string                     | plugin                | host      |
+------------------+-------------------------------------------+-----------------------+-----------+
| root             |                                           | auth_socket           | localhost |
| mysql.session    | \*THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE | mysql_native_password | localhost |
| mysql.sys        | \*THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE | mysql_native_password | localhost |
| debian-sys-maint | \*346F4CD0864E0AF1FE6DB31628588B6C0C9A1703 | mysql_native_password | localhost |
+------------------+-------------------------------------------+-----------------------+-----------+
4 rows in set (0.01 sec)

mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_own_password';
Query OK, 0 rows affected (0.00 sec)

mysql> FLUSH PRIVILEGES;
Query OK, 0 rows affected (0.00 sec)

mysql> exit
```

Login to the database
```
$mysql -u root -p  
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 9
Server version: 5.7.25-0ubuntu0.18.04.2 (Ubuntu)

Copyright (c) 2000, 2019, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.
```

Create a user and give it a strong password

```
mysql> CREATE USER 'yourusername'@'localhost' IDENTIFIED BY 'yourpassword';
Query OK, 0 rows affected (0.02 sec)
```

Grant the new user with appropriate privileges

```
mysql> GRANT ALL PRIVILEGES ON *.* TO 'yourusername'@'localhost' WITH GRANT OPTION;
Query OK, 0 rows affected (0.00 sec)

mysql> exit
```

Start MySQL as a system service
``` 
sudo systemctl start mysql
```

Now we have done the configuration of MySQL

### Install Python Requirements

Install Python3 and pip3 on your system
``` 
sudo apt update
sudo apt install python3 python3-dev
```

Install the required packages using pip3
```
pip3 -r ${PROJ_ROOT_DIR}/requirements.txt 
```

Well done! We have finished all the preparation before emitting the project!


