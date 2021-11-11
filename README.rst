Overview
---------
The basic idea is to provide the ability to generate a custom reputation list
based on our preferences. That way we can blacklist and whitelist whatever
we need to. For example, we could allow the entire AWS IP range if we wanted
to.

Request level configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~
The blocklists used should be configurable per client. They will define what
their requirements are and how paranoid they want to be. In this case "client"
is going to be each indivudal request. You will include the lists you want to
check against as part of the payload.

Overrideable Preferences
~~~~~~~~~~~~~~~~~~~~~~~~
Client blocklist preferences are overrideable by us since they may
be under attack and we'll need to protect ourselves in case of a DDoS. Since
the client will be sending their request over in the payload, we will
make a global "override" list that can be flipped to when we need it.

Blocklists
~~~~~~~~~~
We will by default include the `firehol` level lists by default along with
the `firehol_webserver` list and our own custom list that can be customized
to be more finely tuned to our preferences.

The `firehol` lists are:

- https://iplists.firehol.org/?ipset=firehol_webserver

  The goal of this list is to be used in conjunction with the level lists
  but it should be safe to use in front of a webserver since the clients
  of these IP Addresses should not be interacting with web applications.

  average update: 1 day and 19 minutes

- https://iplists.firehol.org/?ipset=firehol_level1
  The goal for this level is to have no false positives. All IPs listed
  should be known guilty beyond a reasonable doubt.

  average update: 2 hours and 45 minutes

- https://iplists.firehol.org/?ipset=firehol_level2
  This level tracks attacks during the last 48 hours, which means it
  should not include a lot of false positives.

  average update: 17 minutes

- https://iplists.firehol.org/?ipset=firehol_level3
  This list is going beyond attacks and is spyware and viruses as well.
  The reports are from the last 30 days.

  average update: 55 minutes

- https://iplists.firehol.org/?ipset=firehol_level4
  This is the most aggressive of the levels but with that agression it
  will have the highest number of false positives. Not a great list for
  most use cases.

  average update: 10 minutes

They go up in severity from 1 to 4 where level4 will be the most aggressive
and have the most false positives.  These lists are not mutually exclusive
and have very little overlap.  So you can use Level1 and Level4 and skip
Level2 and Level3 if you would like.

The reason I chose these 4 specific lists is because they have a nice level
of tuning where our clients can choose their paranoid level. These are also
a combination of other lists which allows more protection with less monitoring.

Long term we may want to evaluate each list on their own merit and choose
the ones that best fit with our needs.  I did not want to spend too much
time evaluating lists, their benefits, and licenses for the exercise.

Implementation Details
----------------------
**Database**: Redis
The IP datasets we are using are very small:

.. sourcecode:: bash

  32K     firehol_webserver.netset
  44K     firehol_level1.netset
  300K    firehol_level2.netset
  328K    firehol_level3.netset
  1.8M    firehol_level4.netset

So we can fit them in-memory which will also save us on performance.  We could
even store the datasets in memory for each webserver but then we would need to
update each of them individually.

By storing the data in Redis we will have fast in-memory lookups and a central
place for triggering the updates.

**Asynchronous Workers**: Celery

Celery has a scheduler built-in (think cron jobs) and so it will work really
well for us to define how often we want to query and update each list. It also
has a redis backend so this will allow us to utilize infrastructure we already
have in place.

Data Storage
~~~~~~~~~~~~
We want to store the data as IP ranges in Redis, because expanding the
addresses out would require too much data. Our smallest IP list is currently
*2044* lines but 47 million addresses.

I verified that every list we are currently using contains no overlaps and has
used ranges whenever possible (even if its only 2 IPs in the range).  So we can
store ranges per list with a guarantee of no overlap.

I've optimized the for speed of reads.  Updating the data can be slow since we
are mostly concerned with the performance of the reads.

I'm also going to assume removing a range from the dataset individually is
not important. I think we will update the dataset as a whole through the files
or rely on a whitelist service to un-blacklist ranges that are false positives.

**We are only going to support IPv4, not IPv6**

So we will convert an IP address into the integer form:

*192.168.1.1* -> 3232235777

Then we will store that in a sorted set (ZSET) in Redis so we can quickly access
it in *log n*.


To add an ip range into the ZSET we will add the max value of the range to be the
score and we'll store the first item in the list will be the key.  When we fetch
them at the same time we'll be able to compare min-max vs the IP address and
understand if its within the range.

.. sourcecode:: bash

  zadd ip-range 3641996934 3641996934

Then when we fetch this with *ZRANGEBYSCORE* we can compare the score
vs the key to check if the IP is in the range:

.. sourcecode:: bash

   ZRANGEBYSCORE ip-range 3641996436 +inf LIMIT 0 1 WITHSCORES

    1) "3641996934"
    2) "3641996934"

ZRANGEBYSCORE is *O(log(N))*:

- https://redis.io/commands/zrangebyscore

Which seems more than fast enough.  In the largest dataset we are working in,
firehol_level4, it takes 0.003s to query for if an IP Address is in the sorted
set.  If we wanted to optimize this further I could index the max ranges on
these keys but it doesn't seem necessary.

API
---

View Available Lists
~~~~~~~~~~~~~~~~~~~~
To retrieve what lists are available to verify against:

.. sourcecode:: bash
   
  $ curl -v -L -X GET localhost:8000/lists

   [
    {
      "name": "firehol_level4",
      "date_last_modified": "<ISO 8601 Timestamp>",
    },
    {
      "name": "firehol_level2",
      "date_last_modified": "<ISO 8601 Timestamp>",
    },
   ]

Verify IP
~~~~~~~~~
To verify an IP Address against a set of lists:

.. sourcecode:: bash
   
  $ curl -v -L -X GET "localhost:8000/verify?lists=firehol_level1,firehol_level2&ip_address=1.1.1.1"

  {
    "is_bad": false,
  }

The important items here the two query strings:

*lists*: A comma separated list of the lists we want to check the IP address
against.

*ip_address*: The IP Address we want to verify.

In the response we will return an `is_bad` parameter and a `reason` so if the
IP Address is rejected, it will be clear which list rejected it.  This will
allow us to easily identify false positives from lists as well.

Update List
~~~~~~~~~~~
To force an update of a list or to create a custom list you can:

.. sourcecode:: bash

   $ curl -v -L -X PUT --form file='@api/tests/files/firehol_webserver.netset' localhost:8000/lists/firehol_webserver

This will replace the current list with the updated list or create the list if
it does not exist.

This allows us to update the lists off-cycle as well if an important attack has
started to take place.