with work1 as
 ( --—обираем все замены текущего мес€ца
  select id_tu, dt_work, trim(kd_askue) kd_askue, id_schet, kd_work, vl_ras_koeff, pr_koef_transform
    from prom_work wrk
   where wrk.kd_work in (1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 19, 20) -- все кроме сн€ти€
     and wrk.dt_work <=
         last_day((select /*+ no_unnest*/
                   min(dt_beg_period)
                    from prom_period
                   where dt_close_period is null))
     and wrk.dt_work >= trunc((select /*+ no_unnest*/
                               min(dt_beg_period)
                                from prom_period
                               where dt_close_period is null))
  union
  --и на случай если замен в текущем мес€це не было, то берем последнюю работу
  select id_tu, dt_work, trim(kd_askue) kd_askue, id_schet, kd_work, vl_ras_koeff, pr_koef_transform
    from prom_work wrk2
   where wrk2.dt_work = (select max(dt_work)
                           from prom_work wrk1
                          where wrk2.id_tu = wrk1.id_tu))
select (select nm_schema from prom_schema),
       nvl(wrk.kd_askue,(select nm_schema from prom_schema)||'_'||a.nn_abn||'_'||scht.nn_schetch) kd_askue,
       s.kd_pok_zone,
       pz.kd_zone_tp
  from work1 wrk
  join prom_tu_group_assign tga
    on tga.id_tu = wrk.id_tu
   and vl_koef = (select max(vl_koef)
                    from prom_tu_group_assign tga1
                   where tga.id_tu=tga1.id_tu)
  join prom_abonent a
    on tga.id_abn = a.id_abn
  join prom_tu_group tg
    on tg.id_abn = tga.id_abn
   and tg.nn_tu_group = tga.nn_tu_group
   and tg.dt_tu_group_en is null
  join prom_tu_group_tariff tgt
    on tgt.id_abn = tga.id_abn
   and tgt.nn_tu_group = tga.nn_tu_group
  join prom_nsi.prom_sstarf s
    on s.kd_sstr = tgt.kd_sstr
  join prom_nsi.prom_pok_zone pz
    on pz.kd_pok_zone = s.kd_pok_zone
  join prom_dogovor_status_hist dsh
    on dsh.id_abn = tga.id_abn
   and dsh.dt_dogovor_stat = (select max(dt_dogovor_stat)
                                from prom_dogovor_status_hist dsh1
                               where dsh.id_abn = dsh1.id_abn)
   and dsh.kd_dogstat=6
  join prom_reestr r
    on r.id_abn=dsh.id_abn
   and r.dt_reestr_en is null
  join prom_schetch scht
    on scht.id_schet = wrk.id_schet
 --where wrk.kd_askue is null
 group by wrk.kd_askue,
          s.kd_pok_zone,
          pz.kd_zone_tp,
          a.nn_abn,
          scht.nn_schetch
