# Ozma Wiki Full Documentation Bundle

Exported at (UTC): 2026-03-04 15:18:29


## FunQL

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


## FunDB

# FunDB

Source: https://wiki.ozma.io/en/docs/fundb
Exported at (UTC): 2026-03-04 15:18:29

¶ FunDB — ozma.io database

¶ General

FunDB is the database that is the "heart" of our product. It provides query execution, data persistence, permission checking, and much more. An important principle of its work is our approach to customization. All your metadata is also data - all information about schemas, tables, columns, permissions, etc. is the same tables and it is edited on general principles. When you edit them, the database is automatically updated according to your changes.

Each entity has system fields whose values assigned automatically and cannot be set or changed:

- numeric id column. It always exists. It is the master key in SQL terms;

- sub_entity column. It is available for entities that have parent or inherited entities. sub_entity stores the name of an entity subtype for a particular entry as JSON.

Warning: The internal representation of this column is different from JSON and querying its value is a slow operation. Use the OFTYPE and INHERITED FROM statements or virtual fields instead.

¶ System tables structure

System tables is stored in the public schema. They describe the current database settings.

Some tables also have the allow_broken column - when it is set, errors in setting up this entity are not a critical error and only lead to the inoperability of this entity.

Some tables also have an allow_broken column.

Setting the value to true means that errors in setting this entity are not critical and they only lead to the inoperability of this entity.

¶ schemas

Contains generated schemas.

Column
Type
Description

name
string
Schema name. Cannot be empty, contain spaces, strings / and __.

¶ entities

Contains created entities.

Column
Type
Description

schema_id
reference (public.schemas)
The schema (its identifier) containing the entity.

name
string
Entity name. Cannot be empty, contain spaces, strings / and __.

main_field
string
Each entity has a "master column" defined, which is used to briefly describe the entry, e.g. it is using when select entries from lists or for display in tables. If main_field is empty, id is used.

is_frozen
bool
All changes to this entity are prohibited.

is_abstract
bool
An entity is abstract, i.e. you cannot create new records for this entity. Used in conjunction with inheritance.

parent_id
reference (public.entities)
An entity inherits from another entity. When querying for parent entities, child records will also be in the result. Child entities have all the fields of the parent entities, as well as their own fields.

save_restore_key
string
Alternate key (from those given in unique_constraints) that is used to save and restore data from the table. The first key column must be a reference to either public.schemas or another entity with the given save_restore_key. Recursion is not supported.

¶ column_fields

Contains columns for tables.

Column
Description

entity_id
The entity (its identifier) containing the field.

name
Column name. It cannot be empty, contain spaces, strings / and __, be called id or sub_entity.

type
Data type. See datatypes.

default
Default value. It is set in the FunQL language. May be null.

is_nullable
Whether the value in the column can be null.

is_immutable
Whether the data in the column can change after creation.

¶ computed_fields

Contains calculated columns, i.e. columns that are automatically calculated from the values of other columns.

Column
Description

entity_id
The entity (its identifier) containing the field.

name
Column name. It cannot be empty, contain spaces, the strings / and __, be named id or sub_entity.

expression
Expression for the calculated column. Specified as a FunQL language expression (eg "name" || "surname").

is_virtual
Whether it is allowed to override the field expression in child entities. Used to return results based on the subtype of the entry.

is_materialized
Cache the value of a calculated field in the database. Similar to AS MATERIALIZED STORED functionality in PostgreSQL.

¶ unique_constraints

Contains unique constraints, i.e. sets of columns whose values must be unique throughout the table.

Column
Description

entity_id
The entity (its identifier) containing the constraint.

name
The name of the constraint. Cannot be empty, contain spaces, strings / and __.

columns
An array of expressions whose tuples must be unique.

is_alternate_key
Marks the constraint as an alternate key. In some queries to the database, records can be referred not only through id, but also through alternative keys. Alternate keys are also used to save and restore arbitrary entities. Columns included in an alternate key cannot be NULL.

¶ check_constraints

Contains data restrictions, i.e. checks that each row in the table must pass.

Column
Description

entity_id
The entity (its identifier) containing the constraint.

name
The name of the constraint. Cannot be empty, contain spaces, strings / and __.

expression
An expression whose result must be true or null. Specified as a FunQL language expression. Can use the => operator.

¶ indexes

Contains indexes for tables. Used to speed up heavy queries. At the moment, the indexes are fully consistent with the created indexes in PostgreSQL. It is recommended to study Postgres documentation.

Currently, only the trgm indexing operator is supported, which supports strings and gin and gist index types. It creates a trigram index using pg_trgm.

Column
Description

entity_id
The entity (its identifier) containing the index.

name
Index name. Cannot be empty, contain spaces, strings / and __.

expressions
The index is built on an array of these expressions. Collation options can be specified after the expression (as in ORDER BY and index operator class. The currently supported operator class is trgm, which allows you to create GIN indexes for full-text search.

included_expressions
An array of expressions stored within the index. Corresponds to INCLUDE in CREATE INDEX.

is_unique
Whether the index must be unique. This allows for more flexible uniqueness constraints than unique_constraints, but it is not recommended to use an index for this unless uniqueness needs to be checked against expressions.

predicate
Boolean expression for the columns on which the index is built. Corresponds to WHERE in CREATE INDEX.

type
Index type. btree, gist and gin are supported.

¶ user_views

Contains named queries that can be called.

Column
Description

schema_id
The schema (its identifier) containing the user view.

name
Query name. Cannot be empty, contain spaces, strings / and __.

query
Query in FunQL.

¶ user_view_generators

Contains named query generators. You can automatically fill the schema with named queries, for example, by creating on demand for each entity in the table. For schemas with query generators, it is not possible to create additional named queries. A generator is an ECMAScript module that exports a function by default. The signature of generators can be examined in the form of TypeScript signatures here. Requests to the database from the generator are not allowed. The generator takes data about the structure of the database as input.

Column
Description

schema_id
The schema (its identifier) containing the generator.

script
Generator code in JavaScript.

¶ fields_attributes

Contains default attributes for entity fields.

These attributes are automatically added to queries that use the specified fields. This allows users to specify, for example, a single caption for an entity column. Default attributes are set separately for the entities they are bound to. Attributes for the same entity are grouped according to priority.

Column
Description

schema_id
The schema (its identifier) containing the attributes.

field_entity_id
Attributes are set for this entity.

field_name
Attributes are set for this field in field_entity_id.

priority
The default attribute priority by which they are merged in case of conflicts. The lower number corresponds to higher priority.

attributes
Attributes list in the format @{ name1 = value1, name2 = value2 }.

¶ actions

Contains the code of actions -- server-side functions that work within a single transaction. Actions have access to the FunDB API, and they are limited to the role of the user who invoked the action.

An action is an ECMAScript module that exports a handler function by default. The signature of the action functions and the API available internally can be examined in the form of TypeScript signatures here.

The action can take arguments that are passed during the call to FunDB and can return data that will be passed back to the client.

Column
Description

schema_id
The schema (its identifier) containing the action.

function
Action code in JavaScript.

You can check out more information about actions in a separate article.

¶ triggers

Contains a list of triggers that are executed on specified operations.

A trigger is an ECMAScript module that exports a handler function by default. The signatures of the trigger functions and the API available internally can be examined as TypeScript signatures here.

Triggers that execute before an operation (before triggers) can modify the operation's arguments by returning a new args value. If no modifications are needed, return true.

If you return false,  the operation will be considered as cancelled; no further triggers will be fired, but the transaction will be executed to the end.

Column
Description

schema_id
The schema (its identifier) containing the trigger.

trigger_entity_id
The entity whose events the trigger responds to.

name
The name of the trigger. Cannot be empty, contain spaces, strings / and __.

time
Trigger execution time (BEFORE or AFTER the operation).

priority
Trigger execution priority when there are multiple triggers for the same operation.

on_insert
The trigger reacts to the insertion of new records.

on_update_fields
The trigger reacts to change of records. An array that can list field names or *. to respond to changes to any field.

on_delete
The trigger responds to the deletion of records.

procedure
Trigger code in JavaScript.

¶ roles

Contains a list of roles that restrict access to the database. Each role describes the entities and fields to which access is allowed according to the given restrictions. Roles can be inherited from other roles -- inherited permissions are cumulative.

Column
Description

schema_id
The schema (its identifier) containing the role.

name
Role name.

¶ role_parents

Contains relationships between parent roles and child roles. Roles can have multiple parents.

Column
Description

role_id
The role for which the parent (parent_role_id) is defined.

parent_role_id
Parent role.

¶ role_entities

Contains the restrictions set for the given role and entity.

- If restrictions are not defined, access to the entire entity is denied.

- If a restriction on a particular action is not set, the entire action is considered forbidden.

- For full resolution, set the limit to true.

For entities in the same inheritance hierarchy (for example, organizations and people within contacts), accesses are added as "AND" from the root of the hierarchy.

For example, if contacts are constrained to c, organizations to o, and people to p, then the general constraint

c AND (
        sub_entity OF TYPE "people" AND p
    OR sub_entity OF TYPE "organizations" AND o
)

When sampling people, the constraint will simply be

c AND p

Column
Description

role_id
The role containing the restriction.

entity_id
The entity for which the restriction is defined.

insert
Permission to insert records. Requires change permission on at least all required entity fields.

select
SELECT constraint as an expression in FunQL.

update
UPDATE constraint as an expression in FunQL. Additionally, restrictions are imposed from select for the entity and affected fields.

delete
DELETE constraint as an expression in FunQL. Additionally, restrictions are imposed from select for the entity and all its fields. Requires change permission on all entity fields.

check
Check for the admissibility of user changes. Conducted after INSERT and UPDATE queries. Required for INSERT and UPDATE.

¶ role_column_fields

Contains the restrictions that are set for the given role and entity field.

- If restrictions are not defined, access to the entire field is denied.

- If a restriction on a particular action is not set, the entire action is considered forbidden.

- For full resolution, set the limit to true.

The field restrictions are added to the entity restrictions if the field is used in the query.

Column
Description

role_entity_id
The entity constraint containing the field with column_name constraint.

column_name
The field for which the constraint is being defined.

select
SELECT constraint as an expression in FunQL.

insert
Permission to fill in this column in new records.

update
UPDATE constraint as an expression in FunQL.

check
Check for the admissibility of user changes.

¶ users

Contains a list of users who are allowed to access the database.

Column
Description

name
User ID (the email the account was created).

is_enabled
Whether the user is activated.

is_root
Whether the user is a database administrator (full access, including service operations).

role_id
The role that the user belongs to. May be absent (perhaps when the user is an administrator).

¶ events

Contains the event log in the database.

Column
Description

transaction_time
Transaction time.

transaction_id
Unique transaction identifier within the database. Together with "transaction_time" uniquely identifies a transaction in the database.

timestamp
Operation time. Unique within a single transaction.

source
Event source. JSON, where the "source" field is set to "api" (for operations performed by the user) or "trigger" (for operations performed by triggers).

user_name
The user who started the transaction.

type
Event type.

error
The type of error that occurred if the operation failed.

schema_name
The name of the schema for which the event occurred.

entity_name
The name of the entity for which the event occurred.

entity_id
The ID of the record for which the event occurred.

details
Event details in any format.

¶ API

Your database has a public API through which you can interact directly with your data. The base can be used for your own solutions: it does not contain a binding to FunApp (our constructor product), on the contrary - FunApp is built on top of the base, and we use the same public calls.

The API is currently not in a stable version.

Details: FunDB API


## FunDB API

# FunDB API

Source: https://wiki.ozma.io/en/docs/fundb-api
Exported at (UTC): 2026-03-04 15:18:29

¶ FunDB API

The database has a REST API to perform arbitrary operations. All basic actions with the database are performed through this interface, including operations that are performed from the web interface.

Requests are made to the URL corresponding to your instance address, following the pattern: https://YOUR_INSTANCE_NAME.api.ozma.org.

If applicable, the request body must be in JSON format. You need to add the Content-type: application/json header in this case.

Data is returned in JSON format, including errors. For error results, the returned object always contains fields:

- "type": error type (currently only "generic");

- "message": error message.

¶ Authorization

The authorization mechanism and bot accounts will be redesigned in the future.

Authorization in the system is performed according to the OIDC standard. To get your client id and secret, write an email to [email protected].

After receiving the client id and client secret, you can request an authorization token using the username and password of the desired user (grant_type=password). For example, for Python there is a suitable library requests-authlib.

- OIDC automatic configuration URL: https://account.ozma.io/auth/realms/default/.well-known/openid-configuration

- URL to get the token: https://account.ozma.io/auth/realms/default/protocol/openid-connect/token

The token (access token in OIDC) should be sent in HTTP request headers to the API using Authorization: Bearer YOUR_TOKEN.

Example request via curl:

curl \
  -d "client_id=client" \
  -d "client_secret=secret" \
  -d "grant_type=password" \
  -d "username=user" \
  -d "password=password" \
  "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token"

Same request with Python:

import requests

url = "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token"
payload = {
    "client_id": "client",
    "client_secret": "secret",
    "grant_type": "password",
    "username": "user",
    "password": "password"
}

# Make the POST request
response = requests.post(url, data=payload)
response.raise_for_status()
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

To check access rights to the database by token, you can use the GET /check_access request. If the token is valid and it allows access to this database, a 200 OK response will be returned.

The token must be refreshed regularly according to the OAuth standard using refresh_token. It is better to entrust work with a token to a ready-made library for your programming language. An example of an update request via curl:

curl \
  -d "client_id=client" \
  -d "client_secret=secret" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=REFRESH_TOKEN" \
  "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token"

The response comes with a new access_token, and with a new refresh_token.

¶ Receiving data

It is possible to both make queries on existing (named) mappings, and make arbitrary (anonimous) queries. For all user view types, several calls are provided to retrieve data and metadata.

¶ Named user view

Path to user view: /views/by_name/USER_VIEW_SCHEMA/USER_VIEW_NAME.

¶ Anonimous user view

Path to user view: /views/anonymous.

Among the GET parameters, there must be a __query parameter containing the query string.

If you plan to use the query frequently, you will achieve better performance by creating a named query. It is also recommended to use arguments in the query instead of pasting the values directly into the query body. This way the request will be cached and you can avoid code injection attacks.

¶ Receiving data from the database

Query: PATH_TO_THE_USER_VIEW/entries.

Returns: IViewExprResult (see further)

You can pass display arguments to GET request parameters, for example ?id=42. Arguments are encoded as JSON, for example, a string parameter is passed like this: foo="value".

¶ Receiving metadata

Query: PATH_TO_THE_USER_VIEW/info.

Returns: IViewInfoResult (see further)

¶ Returned values

The following TypeScript types describe the format of the returned data:

// Auxiliary types.ber;

export type DomainId = nu
export type RowId = number;
export type FieldName = string;
export type EntityName = string;
export type SchemaName = string;
export type ColumnName = string;
export type AttributeName = string;
export type UserViewName = string;

// Metadata. They are not needed if you only plan to work with previously known queries without changing the data.

export interface IEntityRef {
  schema: SchemaName;
  name: EntityName;
}

export interface IFieldRef {
  entity: IEntityRef;
  name: FieldName;
}

export interface IUserViewRef {
  schema: SchemaName;
  name: UserViewName;
}

export type SimpleType = "int" | "decimal" | "string" | "bool" | "datetime" | "date" | "interval" | "regclass" | "json";

export interface IScalarSimpleType {
  type: SimpleType;
}

export interface IArraySimpleType {
  type: "array";
  subtype: SimpleType;
}

export type ValueType = IScalarSimpleType | IArraySimpleType;

export type FieldValueType = "int" | "decimal" | "string" | "bool" | "datetime" | "date" | "interval" | "json";

export type AttributeTypesMap = Record<AttributeName, ValueType>;

export interface IScalarFieldType {
  type: FieldValueType;
}

export interface IArrayFieldType {
  type: "array";
  subtype: FieldValueType;
}

export interface IReferenceFieldType {
  type: "reference";
  entity: IEntityRef;
  where?: string;
}

export interface IEnumFieldType {
  type: "enum";
  values: string[];
}

export type FieldType = IScalarFieldType | IArrayFieldType | IReferenceFieldType | IEnumFieldType;

export interface IColumnField {
  fieldType: FieldType;
  valueType: ValueType;
  defaultValue: any;
  isNullable: boolean;
  isImmutable: boolean;
  inheritedFrom?: IEntityRef;
}

export interface IMainFieldInfo {
  name: FieldName;
  field: IColumnField;
}

export interface IResultColumnInfo {
  name: string;
  attributeTypes: AttributeTypesMap;
  cellAttributeTypes: AttributeTypesMap;
  valueType: ValueType;
  punType?: ValueType;
  mainField?: IMainFieldInfo;
}

export interface IDomainField {
  ref: IFieldRef;
  field?: IColumnField;
  idColumn: ColumnName;
}

export interface IResultViewInfo {
  attributeTypes: AttributeTypesMap;
  rowAttributeTypes: AttributeTypesMap;
  domains: Record<DomainId, Record<ColumnName, IDomainField>>;
  mainEntity?: IEntityRef;
  columns: IResultColumnInfo[];
}

// Data.

export type AttributesMap = Record<AttributeName, any>;

export interface IExecutedValue {
  value: any; // Value in the cell
  attributes?: AttributesMap;
  pun?: any;
}

export interface IEntityId {
  id: RowId;
  subEntity?: IEntityRef;
}

export interface IExecutedRow {
  values: IExecutedValue[]; // Value in the row
  domainId: DomainId;
  attributes?: AttributesMap;
  entityIds?: Record<ColumnName, IEntityId>;
  mainId?: RowId;
  mainSubEntity?: IEntityRef;
}

export interface IExecutedViewExpr {
  attributes: AttributesMap;
  columnAttributes: AttributesMap[];
  rows: IExecutedRow[];
}

export interface IViewExprResult {
  info: IResultViewInfo;
  result: IExecutedViewExpr;
}

export interface IViewInfoResult {
  info: IResultViewInfo;
  pureAttributes: Record<AttributeName, any>;
  pureColumnAttributes: Record<AttributeName, any>[];
}

For example, the following query returns the result of displaying funapp.settings:

GET /views/by_name/funapp/settings/entries
Authorization: Bearer REPLACE_WITH_YOUR_OIDC_TOKEN

Result:

{
  "info":{
    "attributeTypes":{},
    "rowAttributeTypes":{},
    "domains":{
      "0":{
        "name":{
          "ref":{
            "entity":{
              "schema":"funapp",
              "name":"settings"
            },
            "name":"name"
          },
          "field":{
            "fieldType":{
              "type":"string"
            },
            "valueType":{
              "type":"string"
            },
            "isNullable":false,
            "isImmutable":false
          },
          "idColumn":"name"
        },
        "value":{
          "ref":{
            "entity":{
              "schema":"funapp",
              "name":"settings"
            },
            "name":"value"
          },
          "field":{
            "fieldType":{
              "type":"string"
            },
            "valueType":{
              "type":"string"
            },
            "isNullable":false,
            "isImmutable":false
          },
          "idColumn":"name"
        }
      }
    },
    "columns":[
      {
        "name":"name",
        "attributeTypes":{},
        "cellAttributeTypes":{},
        "valueType":{
          "type":"string"
        }
      },
      {
        "name":"value",
        "attributeTypes":{},
        "cellAttributeTypes":{},
        "valueType":{
          "type":"string"
        }
      }
    ]
  },
  "result":{
    "attributes":{},
    "columnAttributes":[
      {},
      {}
    ],
    "rows":[
      {
        "values":[
          {
            "value":"save_back_color"
          },
          {
            "value":"black"
          }
        ],
        "domainId":0,
        "entityIds":{
          "name":{
            "id":3
          }
        }
      },
      {
        "values":[
          {
            "value":"required_back_color"
          },
          {
            "value":"#F0E5FF"
          }
        ],
        "domainId":0,
        "entityIds":{
          "name":{
            "id":5
          }
        }
      },
      ...
    ]
  }
}

¶ Changing data

All operations with the database are carried out through transactions, which are executed completely and atomically.

Query: POST /transaction

The ITransaction object is passed as the body of the request. If the transaction is successful, an object of type ITransactionResult is returned.

The following TypeScript types describe the format of data sent and returned:

export interface IInsertEntityOp {
  type: "insert";
  entity: IEntityRef;
  entries: Record<FieldName, any>;
}

export interface IUpdateEntityOp {
  type: "update";
  entity: IEntityRef;
  id: number;
  entries: Record<FieldName, any>;
}

export interface IDeleteEntityOp {
  type: "delete";
  entity: IEntityRef;
  id: number;
}

export type TransactionOp = IInsertEntityOp | IUpdateEntityOp | IDeleteEntityOp;

export interface ITransaction {
  operations: TransactionOp[];
}

export interface IInsertEntityResult {
  type: "insert";
  id: number;
}

export interface IUpdateEntityResult {
  type: "update";
}

export interface IDeleteEntityResult {
  type: "delete";
}

export type TransactionOpResult = IInsertEntityResult | IUpdateEntityResult | IDeleteEntityResult;

export interface ITransactionResult {
  results: TransactionOpResult[];
}

For example, an operation to add a new record to the user.test table with the foo field set to 123:

POST /transaction
Authorization: Bearer REPLACE_WITH_YOUR_OIDC_TOKEN
Content-type: application/json

{
  "operations":[
    {
      "type":"insert",
      "entity":{
        "schema":"user",
        "name":"test"
      },
      "entries":{
        "foo":123
      }
    }
  ]
}

Query result:

{
  "results":[
    {
      "type":"insert",
      "id":120
    }
  ]
}

¶ Run action (procedure)

Request: POST /actions/ACTION_SCHEMA/ACTION_NAME/run

POST /actions/marketing/create_list_from_selected_elements/run
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/json
{
    "ids":[26,54,34],
  "list_name":"Clients list"
}

Response:

result contains all the data that was returned by the procedure:

{
    "result": {
        "ok": true
    }
}

or

{
    "result": {
        "ref": {
            "schema": "marketing",
            "name": "list_form"
        },
        "args": {
            "id": 7
        },
        "target": "modal"
    }
}

¶ Check if the instance exists

Request: GET /check_access

GET /check_access
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/json

Python example draft:

response = requests.request(
    "GET",
    "https://" + instance_name + ".api.ozma.org/check_access"
    headers={"Authorization": "Bearer REPLACE_WITH_YOUR_OIDC_TOKEN"},
    json={},
)

If the response is 404, then no such instance exists.

¶ Copy instance schemas

Request: GET /layouts

GET /layouts
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/zip

PUT /layouts
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/zip

Python example draft:

# Download scheme
response = requests.request(
    "GET",
    "https://" + instance_name + ".api.ozma.org/layouts"
    headers={
        "Authorization": "Bearer REPLACE_WITH_YOUR_OIDC_TOKEN",
        "Accept": "application/zip"
    },
    params = {"skip_preloaded":"1"},
)

# Upload cheme to new instance
response_allschemas = requests.request(
    "PUT",
    "https://" + instance_name + ".api.ozma.org/layouts"
    headers={
        "Authorization": "Bearer REPLACE_WITH_YOUR_OIDC_TOKEN",
        "Accept": "application/zip"
    },
    data=response_allschemas.content,
)


## FunApp Menu

# FunApp Menu

Source: https://wiki.ozma.io/en/docs/funapp/menu
Exported at (UTC): 2026-03-04 15:18:29

¶ Menu

¶ Menu

the menu displays the result from one column. This column contains a JSON array with an object that describes the menu.

Menus can have arbitrary nesting levels, however the text size will decrease with each nesting level.

¶ Table of contents

- Attributes

- User view attributes

- Menu object attributes

- Example

- Types of menu references

- Another way to define the menu

- Levels of nesting

Designations:

⚠️ - the attribute is deprecated and no longer supported

Usage:

user view attributes and row attributes start with @ and can be specified anywhere in a SELECT block

column, cell and edit form attributes are specified after the field in the SELECT block in the format field_name @{ attribute = value }

¶ User view attributes

Attribute
Type
Description
Default value

buttons
Array of buttons
Additional buttons in the "kebab menu" and next to it

create_buttons
Array of buttons
If you need to support multiple ways to create an entry and therefore create_link is not appropriate. It will also add buttons to the table header and "kebab menu" with a drop-down list

⚠️extra_actions
Array of actions
Additional buttons in the "kebab menu" on top (⚠️ see buttons)

⚠️help_embedded_page_name
String
Help page title (⚠️ see help_page)

help_page
Link
Link to the help page (funapp.embedded_pages)

menu_centered
Logical
If true menu will be shown directly in the center, or starting from the top of the page if value is false
false

⚠️panel_buttons
Array of actions
Additional buttons on top view bar (⚠️ see buttons)

show_argument_button
Logical
Whether to show by default the "Filters" button that displays the argument editor
false

show_argument_editor
Logical
Whether to show argument editor by default
false

title
String
View title
User view title

type
table, form, board, menu, timeline, multiselect
User view type
table

¶ Menu object attributes

Attribute
Type
Description
Default value

badge
{ value: string, variant?: variant }
An icon with value string that displays next to the menu item. The color is specified using variant.

content
Array with objects of identical structure
When filled in, this field defines the menu item as a category

icon
String
An icon that appears next to the menu item name.
You can use emoji or the material icon name (with underscores instead of spaces).

name
String
Menu item title

ref
Link with identifier
Reference to the user view to which the menu item leads. When filled, this field defines the menu item as a link.

href
External link
External URL. When filled, this field defines the menu item as a link.

size
Number
Specifies the width of the menu item using a 12-cell grid. On mobile devices, this setting is ignored and all elements have a width of 12.
12

¶ Example

SELECT
    @"type" = 'menu',
    @title = 'ozma.io',
    @menu_centered = true,
    @help_page = {
     schema: 'admin',
     name: 'help__user__main_menu'
    },
    @buttons = [{
        name: COALESCE((SELECT __main as name FROM base.people WHERE user = $$user_id LIMIT 1), $$user),
        icon: 'person',
        display: 'desktop',
        ref: &hrm.employee_form,
        target: 'top',
    }],

    "menu",
FROM (
    VALUES ([
        { name: 'Main menu', size: 8, content: [
        	{ name: 'Tasks', size: 3, content: [
                {
                    name: 'My active tasks', icon: 'create',
                    ref: &pm.actions_list,
                    args: {
                            owner: (SELECT array_agg(id) FROM base.people WITH SUPERUSER ROLE WHERE user = $$user_id LIMIT 1),
                            status: (SELECT array_agg(id) FROM pm.actions_stages WHERE name IN ('new', 'in_progress', 'on_hold')),
                            start_date_before: (SELECT $$transaction_time::date)
                        }
                    },
                    {
                        name: 'All tasks', icon: 'app_registration',
                        ref: &pm.actions_table,
                        args: {
                            status: (SELECT array_agg(id) FROM pm.actions_stages WHERE name IN ('new', 'in_progress', 'on_hold')),
                            type: (SELECT array_agg(id) FROM pm.actions_types WHERE name = 'Задача')
                        }
                    },
            ]},
            { name: 'Marketing', size: 3, content: [
                {
                    name: 'Campaigns', icon: 'campaign',
                    ref: &marketing.campaigns_table,
                    badge: {
                        value: (SELECT COUNT(id) FROM marketing.campaigns WHERE stage = (SELECT id FROM marketing.campaigns_statuses WHERE name = 'in_progress')),
                        variant: 'success'
                    }
                },
                {
                    name: 'Lists', icon: 'list',
                    ref: &marketing.lists_table,
                    args: {
                        status: (SELECT id FROM marketing.lists_statuses WHERE name = 'in_progress'),
                    }
                }
            ]},
          ]}
    ])
) AS menu ("menu")

¶ Types of menu references

¶ Reference to any user view

{
    name: 'People',
  icon: 'people',
  ref: &base.people_table,
  args: {
  	status: 'active'
  }
},

Clicking the button redirects to the base.people_table table view. The value status = 'active' is passed as an argument

¶ Reference to entry form

{
    name: 'Person with id=1',
  icon: 'person',
  ref: &base.person_form,
  args: {
  		id: 1
  },
},

Clicking the button redirects to the base.person_form form and show information about person with id = 1

¶ Reference to entry creation form

{
    name: 'Create new Person',
  icon: 'person',
  ref: &base.person_form,
  new: true
},

Clicking the button redirects to the base.people_form form where user can create new person entry

¶ Reference to procedure start

{
    name: 'Update clients data',
  icon: 'settings',
  action: {
  	schema: 'admin',
    name: 'update_data'
  },
  args: {
  	now: (SELECT $$transaction_time)
  }
}

Clicking the button starts the action admin.update_data passing current date and time as an argument with name now

¶ Another way to define the menu

Menus with one level of nesting can also be described by an SQL query with two columns. The text in the columns is used as category and button names. Example:

SELECT
    @type = 'menu',

    category as "сategory_name",
    name @{
        link = ref
    },
FROM
    (
        VALUES
            ('Sales', 'Deals', &crm.deals_table),
            ('Sales', 'Clients', &crm.clients_table),
            ('Sales', 'Tasks', &crm.tasks_board),
            ('Settings', 'Managers', &crm.managers_table),
            ('Settings', 'Admin menu', &admin.main),
    ) as menu (category, name, ref)

¶ Levels of nesting

A menu can have an arbitrary number of nesting levels. The nesting level depends on the text size and menu display style.

¶ First nesting level

SELECT
    @"type" = 'menu',
    "menu",
    @menu_centered = true,
    @title = 'ozma.io',
FROM (
    VALUES ([
        { name: 'Sales', size: 4, content: [
            { icon: 'home', name: 'Deals', ref: &user.menu_ref},
            { icon: 'search', name: 'Clients', ref: &user.menu_ref},
            { icon: 'settings', name: 'Products', ref: &user.menu_ref},
        ]},
        { name: 'Tasks', size: 4, content: [
            { icon: 'favorite', name: 'Dashboard', ref: &user.menu_ref},
            { icon: 'notifications', name: 'My Tasks: board', ref: &user.menu_ref},
            { icon: 'calendar_today', name: 'All Tasks: table', ref: &user.menu_ref},
            { icon: 'mail', name: 'Overdue Tasks', ref: &user.menu_ref},
        ]},
        { name: 'Other', size: 4, content: [
            { icon: 'camera', name: 'Administration', ref: &user.menu_ref},
            { icon: 'shopping_cart', name: 'Settings', ref: &user.menu_ref},
        ]},
    ])) AS menu ("menu")

¶ Second nesting level

SELECT
    @"type" = 'menu',
    "menu",
    @menu_centered = true,
    @title = 'ozma.io',
FROM (
    VALUES ([
        { name: 'Main Menu', size: 10, content: [
            { icon: 'sales', name: 'Sales', size: 4, content: [
            { icon: 'attach_money', name: 'Deals', ref: &user.ref },
            { icon: 'people', name: 'Clients', ref: &user.ref },
            { icon: 'shopping_basket', name: 'Products', ref: &user.ref },
        ]},
        { icon: 'tasks', name: 'Tasks', size: 4, content: [
            { icon: 'dashboard', name: 'Dashboard', ref: &user.ref },
            { icon: 'view_module', name: 'My Tasks: board', ref: &user.ref },
            { icon: 'view_list', name: 'All Tasks: table', ref: &user.ref },
            { icon: 'access_time', name: 'Overdue Tasks', ref: &user.ref },
        ]},
        { icon: 'marketing', name: 'Marketing', size: 4, content: [
            { icon: 'local_activity', name: 'Campaigns', ref: &user.ref },
            { icon: 'list_alt', name: 'Marketing Lists', ref: &user.ref },
        ]},
        { icon: 'contacts', name: 'Contacts', size: 4, content: [
            { icon: 'contact_phone', name: 'Contact Book', ref: &user.ref },
            { icon: 'business', name: 'Organizations', ref: &user.ref },
            { icon: 'person', name: 'People', ref: &user.ref },
            { icon: 'location_on', name: 'Addresses', ref: &user.ref },
        ]},
        { icon: 'administration', name: 'Other', size: 4, content: [
            { icon: 'settings', name: 'Administration', ref: &user.ref },
        ]}
    ]}
    ])) AS menu ("menu")

¶ Nesting levels greated than two

SELECT
    @"type" = 'menu',
    "menu",
    @menu_centered = true,
    @title = 'ozma.io',
FROM (
    VALUES ([
        { name: '', size: 12, content: [
            { name: 'Sales', size: 6, content: [
                { name: 'Deals', size: 6, content: [
                    { icon: 'dashboard', name: 'Dashboard', ref: &user.ref },
                    { icon: 'archive', name: 'Active', ref: &user.ref },
                    { icon: 'unarchive', name: 'Archive', ref:  &user.ref },
                ]},
                { name: 'Clients', size: 6, content: [
                    { icon: 'person', name: 'Active clients', ref:  &user.ref },
                    { icon: 'phone', name: 'Phone Book', ref: &user.ref },
                    { icon: 'hourglass_empty', name: 'In Progress', ref: &user.ref },
                    { icon: 'ac_unit', name: 'Cold Base', ref: &user.ref },
                ]},
            ]},
            { name: 'Production', size: 6, content: [
                { name: 'Storage', size: 6, content: [
                    { icon: 'receipt', name: 'Receipt', ref: &user.ref },
                    { icon: 'assignment', name: 'Write-off', ref: &user.ref },
                    { icon: 'swap_horiz', name: 'Moving', ref: &user.ref },
                    { icon: 'inventory_2', name: 'Inventory', ref: &user.ref },
                ],},
                { name: 'Maintaining', size: 6, content: [
                    { icon: 'build', name: 'Works', ref: &user.ref },
                ]}
            ]}
        ]}
    ])) AS menu ("menu")

¶ See also

- FunApp Web Application - general article about all types of user views

- Table - display the result as a table

- Form - display the result as a custom form

- Kanban board - display the result as kanban boards with cards

- Tree - display the result as a table with a tree structure

- Timeline - display the result as an event log with comments

- Multiselect - display result as multiple values in one control


## FunApp Table

# FunApp Table

Source: https://wiki.ozma.io/en/docs/funapp/table
Exported at (UTC): 2026-03-04 15:18:29

¶ Table

Displays the result as a table.

¶ Table of contents

- Attributes

- User view attributes

- Row attributes

- Column attributes

- Cell attributes

- Edit form attributes

- Example

- Additional information

Designations:

⚠️ - the attribute is deprecated and no longer supported

Usage:

user view attributes and row attributes start with @ and can be specified anywhere in a SELECT block

column, cell and edit form attributes are specified after the field in the SELECT block in the format field_name @{ attribute = value }

¶ User view attributes

Attribute
Type
Description
Default value

buttons
Array of buttons
Additional buttons in the "kebab menu" and next to it

confirm_argument_changes
Logical
Setting the value to true changes the behavior of applying "filters" in the arguments panel - in order for the filters to be applied, you need to click on the "Apply" button
false

create_buttons
Array of buttons
If you need to support multiple ways to create an entry and therefore create_link is not appropriate. It will also add buttons to the table header and "kebab menu" with a drop-down list

create_link
Action
A link to a mapping that can be used to create new entries of this type. Creates a "Add new entry" button in the "kebab menu" and a "+" button in the table header

disable_auto_save
Logical
If true, then timer auto-save is disabled while the view is on the screen (saving will still occur when transitioning between views). Always disabled in views that have triggers on the main entity
false

disable_selection_column
Logical
Remove column used to select rows and delete selected rows action
false

export_to_csv
Logical
Enables the ability to export data of the view to a csv file
false

⚠️extra_actions
Array of actions
Additional buttons in the "kebab menu" on top (⚠️ see buttons)

⚠️help_embedded_page_name
String
Help page title (⚠️ see help_page)

help_page
Link
Link to the help page (funapp.embedded_pages)

lazy_load
Object
Whether to use pagination, currently the only possible value is { pagination: { per_page: 10 } }, which will paginate data into pages of 10 (or any number) records.
Once set of this attribute, you need to refresh the browser page to see the pagination options.

⚠️panel_buttons
Array of actions
Additional buttons on top view bar (⚠️ see buttons)

post_create_link
Action with id
Action to take after a new record is saved

show_argument_button
Logical
Whether to show by default the "Filters" button that displays the argument editor
false

show_argument_editor
Logical
Whether to show argument editor by default
false

show_empty_row
Logical
Show empty string for adding data
true

title
String
View title
User view title

type
table, form, board, menu, timeline, multiselect
User view type
table

¶ Row attributes

Attribute
Type
Description
Default value

row_height
Number
Line height in pixels (as defined in CSS)

¶ Column attributes

Attribute
Type
Description
Default value

caption
String
Column name
Column name from query

column_width
Number
Column width in pixels (as defined in CSS)
200

entry_id
Logical
Indicates that this column contains identifiers for bulk actions
false

fixed
Logical
Fix column. Fixed columns are displayed first and remain visible when scrolling the table horizontally
false

main_reference_field
Logical
A column with this attribute must contain data with type "reference(...)" and must be a column of the main entity. When setting the attribute in conjunction with the select_view attribute, the "Select and Paste" item appears in the table menu, opening a modal window for selecting the associated entity. After selection, a new row is inserted into the table, in which the selected record is automatically set in the cell with this attribute
false

visible
Logical
Column visibility. Using visible with default_value allows you to set default values that are hidden from the user
true

¶ Cell attributes

Attribute
Type
Description
Default value

⚠️cell_color
Color
Cell color (⚠️ use cell_variant)

cell_variant
Option
Cell variant, see color-variants. When using cell_variant as a row attribute, all cells are colored

control
'user_view' | 'iframe'
Indicates the component to use.
When set to user_view, a subview is displayed instead of a cell, corresponding to the value of the cell, interpreted as link with id.
When set to iframe  an iframe is displayed instead of a cell and the value is passed to it.

default_value
Any
The default value for this column. Takes precedence over default for a column in its definition

extra_select_views
Array of links with id
Links to mappings that allow you to select or create related values for this entity. Displays can be called up via the button at the bottom of the list for field values. Required optional attribute "name": 'Action name'

fraction_digits
Number
Only works with number_format, specifies the number of decimal places

link
Action with id
Action that is performed when clicking on a cell

number_format
auto, en, ru
Format for displaying values of int and decimal types.
Example:
Without formatting: 123456.789
en: 123 456.789
en: 123,456.789
When set to auto, the format will be selected based on the user's browser language.

option_variant
Option
Color variant for a solid inside a cell, see color-variants. When using option_variant as a string attribute, all spaces in cells with bool, reference and enum types are colored

options_view
Link
Limits the list of possible entities to only those that are in the view by reference. The view must have a value column (the values in which are equal to the id of the entities that can be selected) and a pun containing label strings that will be used to display options instead of the main entity column.

referenced_entity
Link
Entity reference to use with options_view

row_link
Action with id
The action that is performed when the arrow at the beginning of the line is clicked. If multiple row_link attributes are found, it will be used the link from the last

select_view
Link with id
A special case of extra_select_views, a button for selecting a related entity from the display - convenient when customization of the label on the button is not required and there is only one button

show_seconds
Logical
Whether to show seconds in datetime type cells
false

soft_disabled
Logical
If true, then the cell cannot be edited.
Important: this attribute only disables editing at the interface level, for more severe restrictions, use permissions
false

text_align
left, center, right
Align cell content left, center, right, respectively
numbers - right, others - left

¶ Edit form attributes

Attribute
Type
Description
Default value

control_height
Number
The height of the input field (in px) when editing a cell in a table. Valid only for fields that support text input

text_type
String
Indicates the component type for the string value.

¶ Example

{
    $responsible array(reference(base.people)) null @{
        caption = 'Responsible',
        options_view = &hrm.ref_employees_working_now_view,
    },
    $status array(reference(pm.actions_stages)) null  @{
        caption = 'Status',
        options_view = &pm.ref_active_actions_stages_view,
    },
    $type array(reference(pm.actions_types)) null @{
        caption = 'Action type',
        options_view = &pm.ref_active_actions_types_view,
    }
}:
SELECT
    @type = 'table',
    @title = 'Actionss',
    @buttons = (
        SELECT json_agg({
            name: actions_types.name, icon: 'add_circle',
            ref: &pm.action_form, new: true, target: 'modal',
            default_values: {
                type: actions_types.id,
                stage: (SELECT id FROM pm.actions_stages WHERE name = 'new')
            },
        })
        FROM (
            SELECT id, __main as name
            FROM pm.actions_types
            ORDER BY number
        ) as actions_types
    ),
    @show_argument_button = true,
    @lazy_load = { pagination: { per_page: 25 }},
    @row_link = &pm.action_form,

    @buttons = [{
        name: 'View: table', icon: 'web', variant: 'dark',
        display: 'all',
        buttons: [
            {
                name: 'Table', variant: 'dark', icon: 'table_view',
                ref: &pm.actions_table, target: 'top',
                args: {
                    responsible: $responsible,
                    status: $status,
                    type: $type
                },
            },
            {
                name: 'Board', icon: 'table_chart', variant: 'dark',
                ref: &pm.actions_board, target: 'top',
                args: {
                    responsible: $responsible,
                    status: $status,
                    type: $type
                },
            }
        ],
    }],

    actions.subject @{
        column_width = 450,
    },
    actions.type @{
        column_width = 100,
        options_view = &pm.ref_active_actions_types_view
    },
    actions.sys_related_contact @{
        column_width = 200
    },
    actions.stage @{
        column_width = 125
    },
    actions.start_date @{
        column_width = 130
    },
    actions.due_date @{
        column_width = 130
    },
    actions.responsible_contact @{
        column_width = 225,
        default_value = (SELECT id FROM base.people WHERE user = $$user_id),
    },
    actions.priority @{
        column_width = 100
    },
    actions.created_datetime @{ visible = false },
    actions.created_person @{ visible = false },
    actions.modified_datetime @{ visible = false },
    actions.modified_person @{ visible = false },
    actions.completed_datetime @{ visible = false },
    actions.completed_person @{ visible = false },
    actions.description @{
        column_width = 300,
    },
    actions.parent_action @{
        visible = false
    }
FROM
    pm.actions
WHERE
        NOT actions.is_deleted
    AND ($type IS NULL OR actions.type = ANY(($type)))
    AND ($responsbile IS NULL OR actions.responsible_contact = ANY(($responsible)))
    AND ($status IS NULL OR actions.stage =  ANY(($status)))
ORDER BY
    actions.start_date,
    actions.priority DESC,
    actions.stage DESC,
    actions.id
FOR INSERT INTO
    pm.actions

¶ Additional info

¶ Keyboard shortcuts

Hotkeys
What do

Arrows
Move the cursor if the cell is not open for editing

PgDown/PgUp
Move five lines

Enter/Tab
Work like in Excel or Google.Sheets

Escape
Close cell editing

Delete
Clear cell

Ctrl+c/Ctrl+x/Ctrl+v
Copy/cut/paste

¶ Bulk copy and paste

- The user can copy and paste many cells (for example, from Excel or Google.Sheets), needs to be selected by holding down the mouse button, by Shift+click or by Shift+arrows.

- One copied cell will be pasted into each of the many selected cells

¶ Display boolean values

Non-nullable boolean values in the table are displayed as checkboxes. Nullable boolean values are displayed as a pop-up menu with available values: True, False, NULL

is_nullable
Changing values

true
Choice of three values in the dropdown menu: false, true or null

false
Double clicking on a cell reverses the value

Boolean fields that are supposed to be actively worked with in tables are not recommended to be nullable.

¶ See also

- FunApp Web Application - general article about all types of user views

- Form - display the result as a custom form

- Kanban board - display the result as kanban boards with cards

- Menu - display the result as a set of links

- Tree - display the result as a table with a tree structure

- Timeline - display the result as an event log with comments

- Multiselect - display result as multiple values in one control


## FunApp Form

# FunApp Form

Source: https://wiki.ozma.io/en/docs/funapp/form
Exported at (UTC): 2026-03-04 15:18:29

¶ Form

The view displays the result as a form with blocks.

If more than one row is returned as a result, then a separate form will be rendered for each row.

The form can be used as a container for other views - nested tables, kanban boards, timelines, and also for displaying charts, maps and other components using iframes.

¶ Table of contents

- Attributes

- User view attributes

- Column attributes

- Cell attributes

- Example

Designations:

⚠️ - the attribute is deprecated and no longer supported

Usage:

user view attributes and row attributes start with @ and can be specified anywhere in a SELECT block

column, cell and edit form attributes are specified after the field in the SELECT block in the format field_name @{ attribute = value }

¶ User view attributes

Attribute
Type
Description
Default value

block_sizes
Array of numbers
The number and bllocks width on the form. Width is specified in relative values, 1 is one cell from a 12 cell wide grid. This allows you to set multiple columns on the form and use a simple layout. For example, displaying blocks in two lines with three columns: [4, 4, 4, 4, 4, 4]. Displaying blocks in two lines, the first line has two columns, the second has one block for full width:[4, 8, 12]
[]

buttons
Array of buttons
Additional buttons in the "kebab menu" and next to it

create_buttons
Array of buttons
IIf you need to support multiple ways to create an entry and therefore create_link is not appropriate. It will also add buttons to the table header and "kebab menu" with a drop-down list

create_link
Action
A link to a mapping that can be used to create new entries of this type. Creates a "Add new entry" button in the "kebab menu" and a "+" button in the table header

disable_auto_save
Logical
If true, then timer auto-save is disabled while the view is on the screen (saving will still occur when transitioning between views). Always disabled in views that have triggers on the main entity
false

export_to_csv
Logical
Enables the ability to export data of the view to a csv file
false

⚠️extra_actions
Array of actions
Additional buttons in the "kebab menu" on top (⚠️ see buttons)

⚠️help_embedded_page_name
String
Help page title (⚠️ see help_page)

help_page
Link
Link to the help page (funapp.embedded_pages)

lazy_load
Object
Whether to use pagination, currently the only possible value is { pagination: { per_page: 10 } }, which will paginate data into pages of 10 (or any number) records.
Once set of this attribute, you need to refresh the browser page to see the pagination options.

max_width
Number or string
SSets the maximum width of the form. Width can be given as a number or as a numeric string with or without px (in pixels), with % in percents.
 For example, 500, '500' and '500px' are equivalent and will set the form's maximum width to 500px; '100%' will stretch the form to the full width of the screen at any screen size.
'1140px'

⚠️panel_buttons
Array of actions
Additional buttons on top view bar (⚠️ see buttons)

post_create_link
Action with id
Action to take after a new record is saved

show_argument_button
Logical
Whether to show by default the "Filters" button that displays the argument editor
false

show_argument_editor
Logical
Whether to show argument editor by default
false

title
String
View title
User view title

type
table, form, board, menu, timeline, multiselect
User view type
table

¶ Column attributes

Attribute
Type
Description
Default value

caption
String
Column name. By default, the column name is taken from the query

control_height
Number
The height of the multiline text input box or of the nested view, in px.

form_block
Number
Block number to which this column is attached
0

visible
Logical
Column visibility. Together with default_value allows you to set default values for new entries that are hidden from the user
true

¶ Cell attributes

Attribute
Type
Description
Default value

⚠️cell_color
Color
Cell color (⚠️ use cell_variant)

cell_variant
Option
Cell variant, see color-variants. When using cell_variant as a row attribute, all cells are colored

control
'user_view' | 'iframe'
Indicates the component to use.
When set to user_view, a subview is displayed instead of a cell, corresponding to the value of the cell, interpreted as link with id.
When set to iframe  an iframe is displayed instead of a cell and the value is passed to it.

default_value
Any
The default value for this field. Takes precedence over default for a column in its definition

extra_select_views
Array of links with id
Links to mappings that allow you to select or create related values for this entity. Displays can be called up via the button at the bottom of the list for field values. Required optional attribute "name": 'Action name'

fraction_digits
Number
Only works with number_format, specifies the number of decimal places

link
Action with id
Action that is performed when clicking on a cell

number_format
auto, en, ru
Format for displaying values of int and decimal types.
Example:
Without formatting: 123456.789
en: 123 456.789
en: 123,456.789
When set to auto, the format will be selected based on the user's browser language.

option_variant
Option
Color variant for a solid inside a field, see color-variants. When using option_variant as a string attribute, all spaces in cells with bool, reference and enum types are colored

options_view
Link
Limits the list of possible entities to only those that are in the view by reference. The view must have a value column (the values in which are equal to the id of the entities that can be selected) and a pun containing label strings that will be used to display options instead of the main entity column.

referenced_entity
Link
Entity reference to use with options_view

select_view
Link with id
A special case of extra_select_views, a button for selecting a related entity from the display - convenient when customization of the label on the button is not required and there is only one button

show_seconds
Logical
Whether to show seconds in datetime type cells
false

soft_disabled
Logical
If true, then the field cannot be edited.
Important: this attribute only disables editing at the interface level, for more severe restrictions, use permissions
false

text_align
left, center, right
Align field content left, center, right, respectively. Works only for read-only fields
right for numbers, left otherwise

text_type
'multiline'|'markdown'| wisywig
Sets the component type for the multiline string value.
'multiline'

¶ Example

(
    $id reference(public.entities)
):

SELECT
    @type = 'form', -- How to display the result
    @title = 'Entity: ' || $id=>name,
    @block_sizes = array[ -- Layout blocks on the form
        4, 8,
        12
    ],
    @disabled_auto_save = true,
    @max_width = '100%',

    @buttons = [{
        name: 'Archive',
        icon: 'edit',
        action: &admin.archive_record,
        visible: NOT $id=>is_archived,
        args: {
        	id: $id,
        	is_archived: true
        },
        display: 'desktop'
    }, {
    	name: 'Unarchive',
        icon: 'edit',
        action: &admin.archive_record,
        visible: $id=>is_archived,
        args: {
        	id: $id,
        	is_archived: false
        },
        display: 'desktop'
    }, {
    	name: 'Change History',
    	icon: 'change_history',
    	ref: &admin.change_history,
    	args: {
    		schema: 'public',
        name: 'entities',
        id: $id
    	}
    }],

    schema_id @{
        form_block = 0, -- The input field is located in the block with index 0
        soft_disabled = $id=>is_archived,
        cell_variant = CASE WHEN $id=>is_archived THEN 'light' END
    },
    name @{
        form_block = 0,
        soft_disabled = $id=>is_archived,
        cell_variant = CASE WHEN $id=>is_archived THEN 'light' END
    },
    main_field @{
        form_block = 1,
        soft_disabled = $id=>is_archived,
        cell_variant = CASE WHEN $id=>is_archived THEN 'light' END
    },

    -- Nested user views on the form
    {
    	ref: &admin.unique_constraints_table,
        args: { id: $id }
    } as unique_constraints @{
        control = 'user_view',
        form_block = 0,
    },

    {
    	ref: &admin.column_fields_table,
        args: { id: $id }
    } as column_fields @{
        control = 'user_view',
        form_block = 1,
    },
FROM
    public.entities
WHERE
    id = $id
FOR INSERT INTO
    public.entities

¶ See also

- FunApp Web Application - general article about all types of user views

- Table - display the result as a table

- Kanban board - display the result as kanban boards with cards

- Menu - display the result as a set of links

- Tree - display the result as a table with a tree structure

- Timeline - display the result as an event log with comments

- Multiselect - display result as multiple values in one control


## FunApp Board

# FunApp Board

Source: https://wiki.ozma.io/en/docs/funapp/board
Exported at (UTC): 2026-03-04 15:18:29

¶ Kanban board

Displays the result as a kanban board consisting of the cards grouped by columns.

¶ Table of contents

- Attributes

- User view attributes

- Row attributes

- Column attributes

- Cell attributes

- Example

Designations:

⚠️ - the attribute is deprecated and no longer supported

Usage:

user view attributes and row attributes start with @ and can be specified anywhere in a SELECT block

column, cell and edit form attributes are specified after the field in the SELECT block in the format field_name @{ attribute = value }

¶ User view attributes

Attribute
Type
Description
Default value

board_columns
Array
Specifies the order and presence of columns on the board. For simple boards, where the grouping goes by the text field, it is required to specify the statuses as a string. For complex boards, where the grouping goes by the link field, you need to specify the ID of the required statuses
[]

board_column_width
Number
Column width in pixels

buttons
Array of buttons
Additional buttons in the "kebab menu" and next to it

⚠️card_color
Color
Card color (⚠️ see card_variant)

card_target
String
Determines how the card will open when you click on it. Options are: _modal to open in a modal, _top to open in full page, _blank to open in a new tab
_top

card_create_view
Action
A reference to the user view that can be used to create new entries of this type. Opened by "+" in kanban columns

card_variant
Color option
Card color

confirm_argument_changes
Logical
Setting the value to true changes the behavior of applying "filters" in the arguments panel - in order for the filters to be applied, you need to click on the "Apply" button
false

create_buttons
Array of buttons
If you need to support multiple ways to create an entry and therefore create_link is not appropriate. It will also add buttons to the table header and "kebab menu" with a drop-down list

create_link
Action
A link to a mapping that can be used to create new entries of this type. Creates a "Add new entry" button in the "kebab menu" and a "+" button in the table header

disable_auto_save
Logical
If true, then timer auto-save is disabled while the view is on the screen (saving will still occur when transitioning between views). Always disabled in views that have triggers on the main entity
false

export_to_csv
Logical
Enables the ability to export data of the view to a csv file
false

⚠️extra_actions
Array of actions
Additional buttons in the "kebab menu" on top (⚠️ see buttons)

⚠️help_embedded_page_name
String
Help page title (⚠️ see help_page)

help_page
Link
Link to the help page (funapp.embedded_pages)

⚠️panel_buttons
Array of actions
Additional buttons on top view bar (⚠️ see buttons)

post_create_link
Action with id
Action to take after a new record is saved

show_argument_button
Logical
Whether to show by default the "Filters" button that displays the argument editor
false

show_argument_editor
Logical
Whether to show argument editor by default
false

title
String
View title
User view title

type
table, form, board, menu, timeline, multiselect
User view type
table

¶ Column attributes

Attribute
Type
Description
Default value

board_group
Logical
Specifies that the kanban should be grouped by this field
false

board_order
Logical
Specifies that this field should be manually sorted. For correct operation, the field must be decimal. If this attribute is not specified, then cards are sorted according to any field specified in ORDER BY.
false

¶ Cell attributes

Attribute
Type
Description
Default value

⚠️cell_color
Color
Cell color (⚠️ use cell_variant)

cell_variant
Color option
Cell variant, see color-variants. When used in a kanban card - highlights  the value of a specific record field

default_value
Any
The default value for this column. Takes precedence over default for a column in its definition

icon
String
Adds an icon in front of the specified cell on the card.
You can use emoji or material-icons (with underscores instead of spaces).

row_link
Action with id
The action that is performed when the card is clicked. If multiple row_link attributes are found, the link from the last

visible
Boolean
Controls the field displaying on the card (This attribute required for fields that should be in the request, but should not be displayed on the card)
false

¶ Example

{
    /* Arguments of the user view */
    $responsible array(reference(base.people)) null @{
        caption = 'Responsible',
        /* Available values in popup will be restricted with the results of the specified user view */
        options_view = &base.ref_team_members_view
    },
    $status array(enum('backlog', 'new', 'in_progress', 'done')) null @{
        caption = 'Status',
        text = array mapping
            WHEN 'backlog' THEN 'Ideas'
            WHEN 'new' THEN 'New'
            WHEN 'in_progress' THEN 'In progress'
            WHEN 'done' THEN 'Done'
        END
    },
    $due_date_from datetime null @{
        caption = 'Due date from'
    },
    $due_date_to datetime null @{
        caption = 'Due date to'
    },
    $is_archived bool null @{
        caption = 'Archive'
    },
}:
SELECT
    /* User view type. See also: https://wiki.ozma.io/en/docs/funapp/board */
    @type = 'board',
    /* User view title */
    @title = 'Tasks',
    /* "Filters" panel is hidden by default */
    @show_argument_editor = false,
    /* "Filters" button will be showed on the top of the board */
    @show_argument_button = true,
    /* Reference to the user view opened by clicking the "Open entry in modal" button */
    @row_link = &pm.task_form,
    /* Set the user view used for creating new entries */
    @card_create_view = {
        /* Reference to the user view */
        ref: &pm.task_form,
        /* Default values for the entry being created */
        default_values: {
            responsible_contact: $responsible,
            parent_task: $parent_task
        }
    },
    @card_variant = CASE WHEN priority = 'urgent' THEN 'outline-dark' END,
    subject @{
        /* Color variant using for the field */
        cell_variant = 'outline-info'
    },
    status @{
        /* Group entries by this field */
        board_group = true,
        /* Do not display status field on the card */
        visible = false,
    },
    parent_task @{
        /* Material design icon that will be displayed with the field data on the board card */
        icon = 'account_tree'
    },
    deal @{
        icon = 'tag'
    },
    'Close date: ' || due_date as due_date @{
        icon = 'schedule',
        cell_variant = due_date.@cell_variant
    },
    responsible_contact @{
        icon = 'account_circle'
    },
    "order" @{
        /* Use the value from the "order" field as a sorting number for all entries */
        board_order = true,
        visible = false
    }
     FROM pm.tasks
   WHERE ($is_archived IS NULL OR is_archived = $is_archived)
     AND ($responsible IS NULL OR responsible_contact = ANY($responsible))
     AND ($status IS NULL OR status = ANY($status))
     AND ($due_date_to IS NULL OR due_date <= $due_date_to)
     AND ($due_date_from IS NULL OR due_date <= $due_date_to)
ORDER BY
    "order"

¶ See also

- FunApp Web Application - general article about all types of user views

- Table - display the result as a table

- Form - display the result as a custom form

- Menu - display the result as a set of links

- Tree - display the result as a table with a tree structure

- Timeline - display the result as an event log with comments

- Multiselect - display result as multiple values in one control


## FunApp Tree

# FunApp Tree

Source: https://wiki.ozma.io/en/docs/funapp/tree
Exported at (UTC): 2026-03-04 15:18:29

¶ Tree

This page will be translated soon.

Source page


## FunApp Timeline

# FunApp Timeline

Source: https://wiki.ozma.io/en/docs/funapp/timeline
Exported at (UTC): 2026-03-04 15:18:29

¶ Timeline

This page will be translated soon.

Source page


## FunApp Settings

# FunApp Settings

Source: https://wiki.ozma.io/en/docs/funapp/settings
Exported at (UTC): 2026-03-04 15:18:29

¶ FunApp settings

Here are the supported web application settings.

They are declared in the settings table of the funapp schema

Table "funapp.settings" in  demo instance

¶ Language

language - Instance language (Possible values -en,  ru, es).

¶ Font

font_size — Default font size.

font_size_mobile — Default font size for mobile browsers

¶ Administration

edit_view_query_custom_view - Change the default query editing user view

¶ Contacts for support (email, telegram, whatsapp)

- instance_help_email

- instance_help_telegram

- instance_help_whatsapp

⚙️ Contact for support (email, telegram, whatsapp).

¶ Banner for all users

- banner_message

- banner_important

- show_contact_button_in_banner — URL to contact form. For example, by this setting, you can ask potential clients to fill out the form on your website on demo instances.

- show_invite_button_in_banner

- banner_variant

- banner_background_color

- banner_text_color

⚙️ Add banner

¶ Demo instance settings

- is_read_only_demo_instance

- read_only_demo_instance_get_started_link —  URL to contact form for readonly demo instances. For example, by this setting, you can ask potential clients to fill out the form on your website on demo instances.

- read_only_demo_instance_sign_up_link

- google_tag_manager_container_id

⚙️ Configure demo instance

¶ Color settings

Colors are customized in color variants.

¶ Style Settings

- custom_css - the contents of a CSS file for defining interface styles.

⚙️ Custom CSS Styles

¶ See also

- FunApp user settings

- Home page


## Color Variants

# Color Variants

Source: https://wiki.ozma.io/en/docs/color-variants
Exported at (UTC): 2026-03-04 15:18:29

¶ Color variants and FunApp theme customization

Demo example:

https://x.ozma.org/views/admin/color_variants_table

After clicking on the link,  you can click at the top left burger button and select theme - "Light" or "Dark"

¶ Color variants

Color options are a way to set colors for system components. They are similar to Bootstrap options, but differ in the ability to edit, add additional options, and generate them dynamically.

Color variants are stored in the table funapp.color_variants.

When you create an instance, it will most likely already have color variants, that repeat the options from Bootstrap and support for a dark theme.

The color variant is set by

- name,

- color theme (theme_id),

- background color (background),

- text color (foreground)

- and frame color (border)

but you can set only the background color, the rest of the colors will be selected automatically.

Colors are set similar to CSS. Provided code types:

- hex codes (#aaa, #112233),

- rgb/rgba (rgb(100, 100, 100), rgba(100, 100, 100, 0.5) ) ,

- hsl/hsla (unlike CSS, s and l are set from 0 to 1, not from 0% to 100%)

- and standard html color names (red  , black).

There are "magic" names for magic options that apply to various elements by default:

default — applies to all elements, background and more

interface — applies to top and bottom interface panels

reference — applies to values in multiselects

table

tableCell

kanban

kanbanCard

form

input

button

You can set a coloe variant for each table cell, button, input, and so on  using attributes.

These attributes accept either the name of a variant, such as

cell_variant = "primary"

or dynamically created object, such as

cell_variant = {
    background: '#112233',
  foreground: '#FFFFFF'
}

Possible keys in an object are background, foreground and border, where only background is required. Colors are specified by strings just the same as in the funapp.color_variants.

¶ Color themes

List of available themes are stored in the table funapp.color_themes. Every theme is specified by

- schema (schema_id)

- theme name (name)

- localized name (localized_name)

Localized name format:

{
  "en":"Dark",
  "ru":"Темная"
}

The user can choose a theme from the burger menu (three horizontal bars on the top left).

The chosen theme determines which set of color variants will be used for specific user.

Themes light and dark are "magic".

- light is the default theme. Color variants from light theme will be selected if the theme which user is using doesn't have the desired variant (for example, if the user has the custom theme and userview are using success variant somewhere , but there is no color variant with name success for custom theme, it will be taken from the light theme).

- dark theme will install automatically if the user's browser/OS settings indicate that user prefers the dark theme.
