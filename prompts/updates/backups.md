Let's add admin endpoints for/admin/backups/backup which will do a PG dump on the database if the database is postgrad or I suppose just copy the file if it's sequel light.

/admin/backups/list to get a list of backups

/admin/backups/restore to restore a named backup, or the most recent if not specified.

name the backups with the ISO datetime, second resolution.

/admin/sqlite/export to create sqlite3 file and download it.

/admin/sqlite/import to take an upload of a sqlite3 file and import it.

Move the current JSON import and export to using a ZIP file, and make the interfaces:

/admin/zip/import' and '/admin/zip/export

These will work with a ZIP file of JSON files.

then, make single table imports and exports:

/admin/tables/<table_name>/import
/admin/tables/<table_name>/export

The single table import and exports just read and write JSON

Add the backup directory to the .env config file ( both the .env, and the dev.env and the template ). If the directory is a relative path ( does nto start with '/',) then it should be realtive to the root of the workspace in devel, or realtive to the app.py file in production.