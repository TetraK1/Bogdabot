CREATE OR REPLACE VIEW users as

with userlist_events as (
	select * from events
	where event_name = 'userlist'
)

, adduser_events as (
	select
	event_ts
	, event_data ->> 'name' as username
	, (event_data ->> 'rank')::int as user_rank
	from events
	where event_name = 'addUser' or event_name = 'setUserRank'
)

, userlist_users as (
	SELECT event_ts
	, x.name as username
	, x.rank as user_rank
   FROM userlist_events
   , json_to_recordset(event_data::json) x 
        (name text, rank int)
)

, all_user_updates as (
	select * from adduser_events
	union select * from userlist_users
)

, max_time_updates as (
	select max(event_ts) as event_ts
	, username
	from all_user_updates
	group by username
),

user_ranks as (
select 
	all_user_updates.username
	, all_user_updates.user_rank
from all_user_updates
inner join max_time_updates
on all_user_updates.event_ts = max_time_updates.event_ts
and all_user_updates.username = max_time_updates.username
order by all_user_updates.username asc
)

select * from user_ranks