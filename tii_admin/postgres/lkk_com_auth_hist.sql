--- chart line
select date_trunc('hour', dt_last_auth),count(*) from public.lkk_auth_hist group by date_trunc('hour', dt_last_auth) having 
date_trunc('hour', dt_last_auth) > now()- interval '10 days'
order by 1
-----
--- chart line
select date_trunc('day', dt_last_auth),count(*) from public.lkk_auth_hist group by date_trunc('day', dt_last_auth) having 
date_trunc('day', dt_last_auth) > now()- interval '60 days'
order by 1