CREATE OR REPLACE VIEW chat AS
SELECT
	event_ts as ts,
	to_timestamp(cast (data ->> 'time' as float) /1000) as cy_ts,
	event_data ->> 'username' as username,
	event_data ->> 'msg' as msg
from events
where event = 'chatMsg'