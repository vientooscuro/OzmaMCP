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
