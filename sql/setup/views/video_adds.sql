create or replace view video_adds as(
	with queue_events as (
		select 
		event_ts as ts
		, event_data -> 'item' ->> 'queueby' as from_username
		, event_data -> 'item' -> 'media' ->> 'type' as video_type
		, event_data -> 'item' -> 'media' ->> 'id' as video_id
		, event_data -> 'item' -> 'media' ->> 'title' as video_title
		from events
		where event_name = 'queue'
	)

	select * from queue_events
)