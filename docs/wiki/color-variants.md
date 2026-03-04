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
