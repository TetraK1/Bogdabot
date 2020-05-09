CREATE OR REPLACE VIEW public.videos
 AS
 WITH queue_events AS (
         SELECT events.event_ts,
            ((events.event_data -> 'item'::text) -> 'media'::text) ->> 'type'::text AS video_type,
            ((events.event_data -> 'item'::text) -> 'media'::text) ->> 'id'::text AS video_id,
            (((events.event_data -> 'item'::text) -> 'media'::text) ->> 'seconds'::text)::integer AS video_duration,
            ((events.event_data -> 'item'::text) -> 'media'::text) ->> 'title'::text AS video_title
           FROM events
          WHERE events.event_name = 'queue'::text
        ), playlist_events AS (
         SELECT events.event_ts,
            events.event_name,
            events.event_data
           FROM events
          WHERE events.event_name = 'playlist'::text
        ), playlist_media AS (
         SELECT playlist_events.event_ts,
            item.media ->> 'type'::text AS video_type,
            item.media ->> 'id'::text AS video_id,
            (item.media ->> 'seconds'::text)::integer AS video_duration,
            item.media ->> 'title'::text AS video_title
           FROM playlist_events,
            LATERAL json_to_recordset(playlist_events.event_data::json) item(media jsonb)
        ), all_media AS (
         SELECT playlist_media.event_ts,
            playlist_media.video_type,
            playlist_media.video_id,
            playlist_media.video_duration,
            playlist_media.video_title
           FROM playlist_media
        UNION
         SELECT queue_events.event_ts,
            queue_events.video_type,
            queue_events.video_id,
            queue_events.video_duration,
            queue_events.video_title
           FROM queue_events
        ), grouped_media AS (
         SELECT max(all_media.event_ts) AS event_ts,
            all_media.video_type,
            all_media.video_id
           FROM all_media
          GROUP BY all_media.video_type, all_media.video_id
        ), videos_cte AS (
         SELECT all_media.video_type,
            all_media.video_id,
            all_media.video_duration,
            all_media.video_title
           FROM all_media
             JOIN grouped_media ON grouped_media.video_type = all_media.video_type AND grouped_media.video_id = all_media.video_id AND grouped_media.event_ts = all_media.event_ts
        )
 SELECT videos_cte.video_type,
    videos_cte.video_id,
    videos_cte.video_duration,
    videos_cte.video_title
   FROM videos_cte;