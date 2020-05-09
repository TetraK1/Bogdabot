create or replace view video_plays as (
	select
	event_ts
	, event_data ->> 'type' as video_type
	, event_data ->> 'id' as video_id
	, event_data ->> 'title' as video_title
	from events
	where event_name = 'changeMedia'
)