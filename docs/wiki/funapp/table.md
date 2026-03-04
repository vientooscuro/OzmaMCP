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
