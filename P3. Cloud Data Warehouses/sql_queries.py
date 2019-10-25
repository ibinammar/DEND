import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create= ("""CREATE TABLE staging_events(
        artist              VARCHAR,
        auth                VARCHAR,
        firstName           VARCHAR,
        gender              VARCHAR,
        itemInSession       INTEGER,
        lastName            VARCHAR,
        length              FLOAT,
        level               VARCHAR,
        location            VARCHAR,
        method              VARCHAR,
        page                VARCHAR,
        registration        FLOAT,
        sessionId           INTEGER,
        song                VARCHAR,
        status              INTEGER,
        ts                  TIMESTAMP,
        userAgent           VARCHAR,
        userId              INTEGER 
    )
""")

staging_songs_table_create = ("""CREATE TABLE staging_songs(
        num_songs           INTEGER,
        artist_id           VARCHAR,
        artist_latitude     FLOAT,
        artist_longitude    FLOAT,
        artist_location     VARCHAR,
        artist_name         VARCHAR,
        song_id             VARCHAR,
        title               VARCHAR,
        duration            FLOAT,
        year                INTEGER
    )
""")

songplay_table_create = ("""CREATE TABLE songplays(
        songplay_id         INTEGER         IDENTITY(0,1)   PRIMARY KEY,
        start_time          TIMESTAMP,
        user_id             INTEGER ,
        level               VARCHAR,
        song_id             VARCHAR,
        artist_id           VARCHAR ,
        session_id          INTEGER,
        location            VARCHAR,
        user_agent          VARCHAR
    )
""")

user_table_create = ("""CREATE TABLE users(
        user_id             INTEGER PRIMARY KEY,
        first_name          VARCHAR,
        last_name           VARCHAR,
        gender              VARCHAR,
        level               VARCHAR
    )
""")

song_table_create = ("""CREATE TABLE songs(
        song_id             VARCHAR PRIMARY KEY,
        title               VARCHAR ,
        artist_id           VARCHAR ,
        year                INTEGER ,
        duration            FLOAT
    )
""")

artist_table_create = ("""CREATE TABLE artists(
        artist_id           VARCHAR  PRIMARY KEY,
        name                VARCHAR ,
        location            VARCHAR,
        latitude            FLOAT,
        longitude           FLOAT
    )
""")

time_table_create = ("""CREATE TABLE time(
        start_time          TIMESTAMP       NOT NULL PRIMARY KEY,
        hour                INTEGER         NOT NULL,
        day                 INTEGER         NOT NULL,
        week                INTEGER         NOT NULL,
        month               INTEGER         NOT NULL,
        year                INTEGER         NOT NULL,
        weekday             VARCHAR(20)     NOT NULL
    )
""")

# STAGING TABLES

staging_events_copy = ("""
    copy staging_events from {data_bucket}
    credentials 'aws_iam_role={role_arn}'
    region 'us-west-2' format as JSON {log_json_path}
    timeformat as 'epochmillisecs';
""").format(data_bucket=config['S3']['LOG_DATA'], role_arn=config['IAM_ROLE']['ARN'], log_json_path=config['S3']['LOG_JSONPATH'])

staging_songs_copy = ("""
    copy staging_songs from {data_bucket}
    credentials 'aws_iam_role={role_arn}'
    region 'us-west-2' format as JSON 'auto';
""").format(data_bucket=config['S3']['SONG_DATA'], role_arn=config['IAM_ROLE']['ARN'])

# FINAL TABLES

songplay_table_insert = ("""
insert into songplays (start_time,
                       user_id,
                       level,
                       song_id,
                       artist_id,
                       session_id,
                       location,
                       user_agent)
select staging_events.ts as start_time,
       staging_events.userid as user_id,
       staging_events.level,
       staging_songs.song_id,
       staging_songs.artist_id,
       staging_events.sessionid as session_id,
       staging_events.location,
       staging_events.useragent as user_agent
  from staging_events
  left join staging_songs
    on staging_events.song = staging_songs.title
   and staging_events.artist = staging_songs.artist_name
  left outer join songplays
    on staging_events.userid = songplays.user_id
   and staging_events.ts = songplays.start_time
 where staging_events.page = 'NextSong'
   and staging_events.userid is not Null
   and staging_events.level is not Null
   and staging_songs.song_id is not Null
   and staging_songs.artist_id is not Null
   and staging_events.sessionid is not Null
   and staging_events.location is not Null
   and staging_events.useragent is not Null
   and songplays.songplay_id is Null
 order by start_time, user_id
;
""")

user_table_insert = ("""
insert into users
select user_id::INTEGER,
       first_name,
       last_name,
       gender,
       level
  from (select userid as user_id,
               firstname as first_name,
               lastname as last_name,
               gender,
               level
          from staging_events
         where user_id is not Null) as temp
 group by user_id, first_name, last_name, gender, level
 order by user_id;
""")

song_table_insert = ("""
INSERT INTO songs (song_id, title, artist_id, year, duration)
SELECT DISTINCT song_id, title, artist_id, year, duration
  FROM staging_songs;
""")

artist_table_insert = ("""INSERT INTO artists (artist_id, name, location, latitude, longitude)
SELECT DISTINCT artist_id, artist_name, artist_location, artist_latitude, artist_longitude
  FROM staging_songs;
""")

time_table_insert = ("""
insert into time
select start_time,
       date_part(hour, start_time) as hour,
       date_part(day, start_time) as day,
       date_part(week, start_time) as week,
       date_part(month, start_time) as month,
       date_part(year, start_time) as year,
       date_part(weekday, start_time) as weekday
  from (select ts as start_time
          from staging_events
         group by ts) as temp
 order by start_time;
""")

time_table_Select= ("""
select * from time
limit 5;
""")


# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
select_table_queries = [time_table_Select]

#