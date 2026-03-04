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
