with base as (

    select * from {{ ref('stg_google_trends') }}
    where not is_partial

)

select week_start, 'depression' as keyword, depression as interest_score from base
union all
select week_start, 'angst'      as keyword, angst      as interest_score from base
union all
select week_start, 'burnout'    as keyword, burnout    as interest_score from base
union all
select week_start, 'therapie'   as keyword, therapie   as interest_score from base
union all
select week_start, 'psychologe' as keyword, psychologe as interest_score from base

order by week_start, keyword
