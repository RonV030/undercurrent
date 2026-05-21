with source as (

    select * from {{ source('raw', 'google_trends') }}

),

renamed as (

    select
        cast(date        as date)    as week_start,
        cast(depression  as integer) as depression,
        cast(angst       as integer) as angst,
        cast(burnout     as integer) as burnout,
        cast(therapie    as integer) as therapie,
        cast(psychologe  as integer) as psychologe,
        cast("isPartial" as boolean) as is_partial

    from source

)

select * from renamed
