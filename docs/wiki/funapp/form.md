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
