select
    name,
    total(dur) as total
from
    (
        select
            ts,
            dur,
            cpu,
            end_state,
            priority,
            process.name,
            thread.name
        from
            sched_slice
            left join thread using(utid)
            left join process using(upid)
    )
group by
    name
order by
    total desc