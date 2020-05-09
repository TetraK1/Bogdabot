create or replace view quotes as (
	select *
	from chat
	where
	msg not like '/%'
	and username not like '%vidyabot%'
	and msg not like '$%'
	and char_length(msg) > 30
)