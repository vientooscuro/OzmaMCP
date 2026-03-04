# FunQL

Source: https://wiki.ozma.io/en/docs/funql
Exported at (UTC): 2026-03-04 15:18:29

¶ FunQL - ozma.io query language

¶ General principles

The FunQL query language is based on the SQL dialect of the PostgreSQL database (more precisely, only the DQL parts, in other words, only the SELECT command is supported). Additionally added:

- Syntax of functions;

- Syntax of attributes;

- Other syntax extensions.

The documentation assumes that you use PostgreSQL documentation to get acquainted with the basics of the query language.

The language is under development, so many standard SQL constructs are not yet supported. We are gradually adding support for new constructs; if you need more operators or constructs that we don't support yet, let us know!

¶ Data types

¶ Strings (string)

For example,'Hello!'.

The format is the same as the PostgreSQL extended string format (E prefix), in other words -- escape expressions like C are supported.

¶ Integer numbers (int)

For example, 42.

32-bit precision is used.

¶ Floating point numbers (decimal)

For example, 3.14.

Note. Although numbers are stored in the database in arbitrary precision format, internally FunDB currently uses 128-bit numbers to convert them. This still provides sufficient accuracy for financial transactions. In FunApp, on the other hand, the standard JavaScript number data type is used to display numbers, which provides only 64-bit precision. If this accuracy is not enough for you, please let us know - in the future we plan to switch to "honest" numbers with arbitrary precision in our API and in the web application.

The round function is supported to the nearest integer or to N decimal places round().

¶ Boolean values (bool)

true or false. Character case is not important (like in standard SQL).

¶ Date (date)

Specified via a type conversion operator, e.g. '2019-01-01' :: date. Do not depend on the time zone.

¶ Date and time (datetime)

Specified via a type conversion operator, e.g. '2019-01-01 08:00' :: datetime. It is always set in UTC.

¶ Interval (interval)

The time interval is also specified via a type conversion operator: for example '12 days' :: interval. All job formats supported by PostgreSQL are also supported in FunQL.

¶ Arrays (array(item_type))

Arrays in FunQL use PostgreSQL array syntax, such as array [1, 2, 3]. It supports only one degree of depth (i.e. nested arrays are not allowed). An array type can also be specified via a type conversion operator, e.g. array[]::array(int).

¶ JSON objects and lists (json)

JSON objects have a dedicated special syntax that allows you to specify parts of an array through expressions.

For example: { "foo": 1 + 2 } or [ 1 + 2, 'foo' ]. You can use arbitrary expressions, including values from table cells inside the object.

¶ Unique UIDs (uuid)

Used to store identifiers in UUID format.

¶ References (reference(entity_name))

References to other entities. They are numeric identifiers id from the records of the given entity. An entity is specified by an identifier.

¶ Enumerated type (enum(val1, val2...))

A value with fixed string options. Variants are specified as strings. Columns and arguments of this type are subject to appropriate checks. The values are processed and displayed in the specified order.

- Attributes for field values of an enumerated type

¶ Files

In the near future

The file will be a separate record type.

¶ Query structure

Syntax:

[ { arg_name :: type [ NULL ] [ DEFAULT value ] [ @{ ... } ], ... }: ]

SELECT ...
[ FOR INSERT INTO entity_name ]

Query example:

{
    $id reference(usr.orders)
}:

SELECT
        -- How to show query result
    @"type" = 'form',

    -- Widths of form blocks in a 12-cell grid
    -- Blocks that do not fit - wrap to the next line
    @"block_sizes" = array[
        7, 5,
        12
    ],

    number @{
    		-- Block index from the `block_sizes` argument
        "form_block" = 1
    },
    order_datetime @{
        "form_block" = 0
    },
    client @{
        "form_block" = 0
    },
    status @{
        "form_block" = 1
    },
    -- Nested user view definition
    {
        ref: &usr.goods_for_order_table_conn,
        args: {
            id: $id
        }
    } as goods_in_order @{
        "control" = 'UserView',
        "form_block" = 2,
        "caption" = 'Goods In Order'
    }
FROM
    usr.orders
WHERE
    id = $id
FOR INSERT INTO
    usr.orders

¶ Identifiers

Identifiers follow standard SQL syntax, eg. "schemas" or just schemas.

You can specify __main, which means "main column" instead of specifying a column name. See FunDB for details on the main column.

¶ Arguments

Designate external values that are passed to the request.

{
     $my_argument int,
     $my_second_argument string
}:

Argument names use standard SQL identifier syntax. Within a query, arguments can be referred as $arg_name (eg. $id).

¶ DEFAULT - default value

Arguments can have default values via the DEFAULT <value> construct:

{
     $my_argument int DEFAULT 0
}:

¶ NULL - optional argument

Arguments can be optional (option NULL):

{
     $my_optional_argument int NULL
}:

¶ Argument editor

Arguments can be changed dynamically using the argument editor.

¶ Attributes

Used only to change the display of arguments in the argument editor.

Arguments can have attributes, they are similar to cell attributes, but they cannot use dynamic values.

{
    $my_argument int @{ caption: 'my argument' }
}:

¶ Global arguments

There are also global arguments that are always passed to the request. Global arguments are referenced via $$global_name.

Their list:

Argument
Description

$$lang
current user language in BCP 47 format, for example 'ru-RU'

$$user
current username (user's e-mail)

$$user_id
the current user id in the "public"."users" table. Can be NULL

$$transaction_time
start time of the current transaction

The argument can be optional if given with the NULL keyword. It is optional to fulfill the request in this case; if the argument is absent, it will be equal to NULL.

¶ SELECT

In FunQL SELECT ... is a DQL SELECT with standard constructs and additions. Not all PostgreSQL constructs are currently implemented. Current syntax:

SELECT [ select_expression ] [, ...]
    [ FROM from_item [, ...] ]
    [ WHERE condition ]
    [ { UNION | INTERSECT | EXCEPT } [ ALL | DISTINCT ] select ]
    [ GROUP BY grouping_element [, ...] ]
    [ ORDER BY expression [ ASC | DESC ] [, ...] ]
    [ LIMIT count ]
    [ OFFSET start ]

, where select_expression is one of:

  @ attribute_name = expression
    expression [ AS output_name ] [ @{ [ attribute_name = expression ] [, ...] } ]

, from_item is one of:

    table_name
    ( select ) AS alias
        ( values ) AS alias ( column_alias [, ...] )
    from_item join_type from_item ON join_condition

, join_type is one of:

  [ INNER ] JOIN
  LEFT JOIN
  RIGHT JOIN

, values is:

VALUES ( expression [, ...] ) [, ...]

In FunQL, you cannot specify a default schema, i.e. all tables must explicitly specify a schema, such as public.entities.

¶ Attributes

Attributes allow you to specify options for displaying the request. For example, you can specify the column width of the column  in table. Attributes  of several types. See Funapp wiki for details on attributes supported by FunApp.

¶ Row attributes

Specified as @name = value. Applies to the entire line. If cell identifiers are not used in the value, then the attribute applies to the entire request (and they are called request attributes).

¶ Cell attributes

Given for a specific cell as column_name @{ name = value }. If the value does not use cell identifiers, then the attribute is applied to the column (and it is called the column attribute).

¶ Pure attributes

In the case where only user view information is requested (for example, when creating new records in FunApp), there are no values from real entities and no arguments are available.

Accordingly, attributes of rows and cells that use any identifiers cannot be calculated and are not returned. Attributes that are given by simple expressions, including attribute values without mentioning the presentation arguments, are called pure - such attributes are always calculated.

The display of the view in FunApp may differ for new entries and for existing entries because of this.

For example:

@"type" = 'form'

will work either way, but:

@"type" = $type

will not work in FunApp when creating a new entry.

¶ Source tracking

FunQL keeps track of the sources of selected columns, which allows you to edit their values directly from the query result in FunApp.

You don't need to do anything extra for this - any mention of columns without additional expressions above them, for example SELECT "name" AS "user_view_name" FROM "public"."user_views", allows you to edit cells (in this case, the name of the view).

Any operations on a column, eg. "foo" + 0 makes it untracked - such columns cannot be edited. Computable columns cannot be edited either, see FundDB table structure for details.

¶ Main entity

It specified via FOR INSERT INTO entity_name. If the main entity is specified, it is checked that the specified entity and all of its required columns can be selected in the query. In this case, additional information about the selected columns is returned as part of the query result, and in FunApp it becomes possible to create new records in the table directly from the result of this query.

An entity can be distinguished if:

- It is the only one in the FROM clause;

- It is the left operand in LEFT JOIN, or it is  the right operand in RIGHT JOIN;

- It is the only selectable entity in the subquery.

¶ Operators and expressions

The behavior of these operators is the same as in PostgreSQL, with a few exceptions.

- NOT;

- AND;

- OR;

- || (string concatenation);

- =;

- != and <>;

- LIKE and NOT LIKE (~~ and !~~);

- <, <=, > >=;

- +, -, *, /;

- IN (values, ...) and NOT IN (values, ...);

- IN (subquery) and NOT IN (subquery);

- IS NULL, IS NOT NULL;

- IS DISTINCT FROM, IS NOT DISTINCT FROM;

- CASE;

- COALESCE;

- :: (type conversion). It does not support the conversion of scalars to arrays and vice versa;

- -> and ->> (getting elements of JSON objects and arrays).

¶ Aggregate functions

The following aggregate functions are supported:

- sum;

- avg;

- min;

- max;

- count;

- bool_and.

You can read detailed documentation on them on the PostgreSQL website. If you need features that we haven't added yet - write to us!

¶ Other functions

The following functions are allowed and their behavior corresponds to the behavior in PostgreSQL:

¶ Math functions

Function
Result type
Description
Example
Result

abs(x)
argument type
number module
abs(-17.4)
17.4

round(decimal)
argument type
rounding to the nearest integer
round(42.4)
42

round(v decimal, s integer)
decimal
rounding v to s decimal places
round(42.4382, 2)
42.44

¶ String functions and operators

Function
Result type
Description
Example
Result

substr(string, from [, count])
string
Extracts a substring
substr('alphabet', 3, 2)
ph

split_part(string, delimiter, position)
string
Splits a string on a specified delimiter
split_part('one, two, three', ',' 2)
two

¶ Date/time functions and operators

Function
Result type
Description
Example
Result

age(datetime)
interval
Subtracts the date/time from current_date (midnight of the current day)
age('1957-06-13'::datetime)
43 years 8 mons 3 days

date_part(text, datetime)
decimal
Returns a date field
date_part('day', '2001-02-16'::datetime)
16

date_part(text, interval)
decimal
Returns a date field
date_part('month', '2 years 3 months')::interval
3

date_trunc(text, datetime)
datetime
Trims date components to specified precision
date_trunc('hour', '2001-02-16 20:38:40'::datetime)
2001-02-16 20:00:00

date_trunc(text, interval)
interval
Trims date components to specified precision
date_trunc('hour', '2 days 3 hours 40 minutes'::interval)
2 days 03:00:00

isfinite(date)
bool
Checks if the date is finite (not +/- infinity)
isfinite('2001-02-16'::date)
true

isfinite(datetime)
bool
Checks for the finiteness of time (its difference from +/- infinity)
isfinite('2001-02-16 21:28:30'::datetime)
true

isfinite(interval)
bool
Checks if the interval is finite
isfinite('4 hours'::interval)
true

¶ Data formatting functions

Function
Result type
Description
Example

to_char(datetime, text)
string
converts time to text
to_char('2020-05-01 15:35:00'::datetime, 'HH12:MI:SS')

to_char(interval, text)
string
converts interval to text
to_char('15h 2m 12s'::interval, 'HH24:MI:SS')

to_char(integer, text)
string
converts integer to text
to_char(125, '999')

to_char(decimal, text)
string
converts single/double precision float to text
to_char(125.8, '999D9')

If you need features that we haven't added yet - write to us!

¶ Additional extensions

¶ User view references

It is specified as &user_view_name (or &schema.user_view_name). Used in particular attributes to refer to other user views. Such links are checked for validity, i.e. you cannot refer to a non-existent mapping.

If schema is not specified for the mapping, it will be used the schema in which the mapping resides.

The reference &"public"."events" is equivalent to the JSON object { "schema": 'public', "name": 'events' }.

¶ Operator =>

Relationship dereferencing operator. Can be used to get data of arbitrary depth, e.g.:

SELECT
column_fields.entity_id=>schema_id=>name
FROM
column_fields

Currently, such expressions are prohibited in ON expressions for JOIN.

¶ Privileged tables and columns

Use this functionality with care to avoid data leakage.

Tables in a query can be marked as privileged, for example: FROM base.contacts WITH SUPERUSER ROLE. This allows you to skip the restriction of visible records in the table according to access rights.

The ! operator marks the column as privileged. Access rights are also not applied to such columns, that is, their values are not hidden. The operator can be combined with the => operator so that no restrictions apply to the entire joined table. For example, in the expression foo!=>bar the value bar will be visible to all users. If bar is a link field, then to avoid filtering when displaying the main field, use ! on bar: foo!=>bar!.

This functionality is useful if access restrictions lead to slow queries, and the administrator is sure that in a particular case they can be neglected (for example, in aggregating queries).

¶ INHERITED FROM and OFTYPE expressions

These expressions allow you to check the type of a particular record. "contacts"."sub_entity" INHERITED FROM "prganizations" will return TRUE if the entry is of type "organizations" or any type derived from it. "contacts"."sub_entity" TYPEOF "organizations will only return TRUE if the entry is of type "organizations" itself. The use of the OFTYPE operator is generally not recommended; use it only if you are sure you need to specify INHERITED FROM expression type allows you to write expressions that will continue to work when new types are added to the inheritance hierarchy.

After type checks, columns that only exist in the legacy table become available. For example, if the first_name column exists only in the people child of the contacts table, then the expression SELECT CASE WHEN "contacts"."sub_entity" INHERITED FROM "people" THEN "contacts"."first_name" ELSE 'No name' END FROM "base"."contacts" will work even though there is no first_name column in the contacts table.

¶ .@ и .@@ operators fetching attribute values

foo.@caption fetches the value of caption attribute for a field foo.

bar.@@type fetches the value of type attribute for an entity bar.

{
    $enum_arg enum('foo', 'bar') null @{
        caption = 'Тест',
        text = mapping
            when 'foo' then 'Foo'
            when 'bar' then 'Bar'
        end,
        attr1 = mapping
            when 'foo' then 42
            when 'bar' then 73
            else 1337
        end,
    }
}:

SELECT

        /* .@text returns 'Foo ' or 'Bar ' */
       @title = $enum_arg.@text || ' демо',

        /* $enum_arg value
          -> returns 'foo' or 'bar' or NULL */
       $enum_arg as enum_arg,

        /* attr1 attribute value
          -> returns 42 or 73 or NULL */
       $enum_arg.@attr1 AS enum_arg_attr @{
           test2 = mapping
        	   when 42 then 'cool'
        	   when 73 then 'cooler'
           end
       },

        /* returns cell_variant value for a specific action status */
       action=>stage.@cell_variant AS stage_attr @{
           cell_variant = action=>stage.@cell_variant,
       },

        /* stage caption value stored in "actions.stage" default attributes */
       stage.@caption AS caption_attr,

        /* foo attribute value from the joined table "actions" */
       actions.@@foo AS foo_attr

  FROM pm.actions_for_contacts
  LEFT JOIN (SELECT @foo = 123, id, stage
  			    FROM pm.actions) AS actions
        ON actions_for_contacts.action = actions.id

- Use case
