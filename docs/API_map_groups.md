# API Documentation for Map Groups

Disclaimer: This document was bootstrapped using Github Copilot and GPT-4o. The content has been re-written for accuracy.

The Map Groups module uses JavaScript Object Notation - Remote Procedure Call ('JSON-RPC') 2.0 to manage its API.

In brief, this means all RPC API calls for the Madrona portal this module is included in, as well as for any other modules that use RPC, use the same endpoint: `/rpc`.

The requests to this endpoint should be structured with the following request content:
```
{
    id: (int),
    jsonrpc: 2.0,
    method: (string),
    params: (array)
}
```
Use the documentation below to identify which `method` value to use, what `id` is used to represent, and whether any parameters should be included in your `params` array.

## JSON-RPC endpoint for mapgroups

You may view a summary of all RPC methods available on a given Madrona Portal instance by opening the `/rpc` endpoint in a browser (no request content needed).

### method: get_sharing_groups

**Description:** Retrieves the sharing groups for the logged-in user.
- requires a valid CSRF token and sessionid in the cookies

**Request Body:**
- Required:
   - `method:'get_sharing_group'`: Tells RPC to use this method.
- Optional:
   - `id`: does nothing
   - `jsonrpc`: supports 2.0 by default
   - `params`: empty array by default (none available)

**Returns:** A list of sharing groups with the following fields:
- `group_name`: The name of the group.
- `group_slug`: The slug of the group.
- `members`: A list of members in the group.
- `is_mapgroup`: A boolean indicating if it is a map group.

**Example Response:**
```json
{
    "jsonrpc": "2.0",
    "id": "",
    "result": [
        {
            "group_name": "Testing",
            "group_slug": "testingQB55t05q",
            "members": [
                "Bill",
                "Ted"
            ],
            "is_mapgroup": true
        },
        {
            "group_name": "A private group",
            "group_slug": "a-private-groupTIG1doWy",
            "members": [
                "Bill"
            ],
            "is_mapgroup": true
        },
        {
            "group_name": "Share with Public",
            "group_slug": "Share with Public",
            "members": [],
            "is_mapgroup": false
        }
    ]
}
```

### method: update_map_group [DEPRECATED]

**Description:** Updates the details of a map group.
- requires a valid CSRF token and sessionid in the cookies

**Parameters:**
- `group_id`: The ID of the group to update.
- `options`: A dictionary of options to update.
- `kwargs`: Additional keyword arguments.


