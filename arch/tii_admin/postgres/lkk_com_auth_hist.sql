--- chart line
/** ## LKK authentication minutely **/
select date_trunc('minute', dt_last_auth),count(*) from public.lkk_auth_hist group by date_trunc('minute', dt_last_auth) having 
date_trunc('minute', dt_last_auth) > now()- interval '180 minute'
order by 1;

--- chart line
/** ## LKK authentication hourly **/
select date_trunc('hour', dt_last_auth),count(*) from public.lkk_auth_hist group by date_trunc('hour', dt_last_auth) having 
date_trunc('hour', dt_last_auth) > now()- interval '10 days'
order by 1;

--- chart line
/** ## LKK authentication daily **/
SELECT date_trunc('day', dt_last_auth),count(*) from public.lkk_auth_hist group by date_trunc('day', dt_last_auth) having 
date_trunc('day', dt_last_auth) > now()- interval '60 days'
order by 1;

--- chart bar
/** ## LKK authentication monthly **/
select date_trunc('month', dt_last_auth),count(*) from public.lkk_auth_hist group by date_trunc('month', dt_last_auth) having 
date_trunc('month', dt_last_auth) > now()- interval '365 days'
order by 1;