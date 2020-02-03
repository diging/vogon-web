REPO_CONFIG = """
{
    "name": "Amphora",
    "description": "Amphora digital repository",
    "documentation": "http://diging.github.io/amphora",
    "endpoint": "https://amphora.asu.edu/amphora/rest",
    "methods": [
        {
            "name": "list",
            "method": "GET",
            "path": "{endpoint}/resource/",
            "parameters": [
                {
                    "accept": "limit",
                    "send": "limit",
                    "required": false
                },
                {
                    "accept": "offset",
                    "send": "offset",
                    "required": false
                },
                {
                    "accept": "content_type",
                    "send": "content_type",
                    "required": false
                }
            ],
            "response": {
                "type": "json",
                "path": "",
                "parameters": [
                    {
                        "name": "count",
                        "path": "count"
                    },
                    {
                        "name": "next",
                        "path": "next"
                    },
                    {
                        "name": "previous",
                        "path": "previous"
                    },
                    {
                        "name": "resources",
                        "path": "results",
                        "type": "object",
                        "config": {
                            "path": "*",
                            "parameters": [
                                {
                                    "name": "title",
                                    "path": "name",
                                    "type": "text",
                                    "display": "Name"
                                },
                                {
                                    "name": "content_types",
                                    "path": "content_types"
                                },
                                {
                                    "name": "url",
                                    "path": "url",
                                    "type": "url",
                                    "display": "URL"
                                },
                                {
                                    "name": "uri",
                                    "path": "uri",
                                    "type": "url",
                                    "display": "URI"
                                },
                                {
                                    "name": "id",
                                    "path": "id",
                                    "type": "int",
                                    "display": "ID"
                                },
                                {
                                    "name": "public",
                                    "path": "public",
                                    "type": "bool",
                                    "display": "Public"
                                }
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "search",
            "method": "GET",
            "path": "{endpoint}/resource/",
            "parameters": [
                {
                    "accept": "query",
                    "send": "search",
                    "required": true
                },
                {
                    "accept": "limit",
                    "send": "limit",
                    "required": false
                },
                {
                    "accept": "offset",
                    "send": "offset",
                    "required": false
                },
                {
                    "accept": "content_type",
                    "send": "content_type",
                    "required": false
                }
            ],
            "response": {
                "type": "json",
                "path": "",
                "parameters": [
                    {
                        "name": "count",
                        "path": "count"
                    },
                    {
                        "name": "next",
                        "path": "next"
                    },
                    {
                        "name": "previous",
                        "path": "previous"
                    },
                    {
                        "name": "resources",
                        "path": "results",
                        "type": "object",
                        "config": {
                            "path": "*",
                            "parameters": [
                                {
                                    "name": "title",
                                    "path": "name",
                                    "type": "text",
                                    "display": "Name"
                                },
                                {
                                    "name": "url",
                                    "path": "url",
                                    "type": "url",
                                    "display": "URL"
                                },
                                {
                                    "name": "uri",
                                    "path": "uri",
                                    "type": "url",
                                    "display": "URI"
                                },
                                {
                                    "name": "id",
                                    "path": "id",
                                    "type": "int",
                                    "display": "ID"
                                },
                                {
                                    "name": "content_types",
                                    "path": "content_types"
                                },
                                {
                                    "name": "public",
                                    "path": "public",
                                    "type": "bool",
                                    "display": "Public"
                                }
                            ]
                        }
                    }

                ]
            }
        },
        {
            "name": "collections",
            "method": "GET",
            "path": "{endpoint}/collection/",
            "parameters": [],
            "response": {
                "type": "json",
                "path": "results/*",
                "parameters": [
                    {
                        "name": "name",
                        "path": "name",
                        "type": "text",
                        "display": "Name"
                    },
                    {
                        "name": "url",
                        "path": "url",
                        "type": "url",
                        "display": "URL"
                    },
                    {
                        "name": "uri",
                        "path": "uri",
                        "type": "url",
                        "display": "URI"
                    },
                    {
                        "name": "id",
                        "path": "id",
                        "type": "int",
                        "display": "ID"
                    },
                    {
                        "name": "description",
                        "path": "description"
                    },
                    {
                        "name": "public",
                        "path": "public",
                        "type": "bool",
                        "display": "Public"
                    },
                    {
                        "name": "size",
                        "path": "size",
                        "type": "int",
                        "display": "Number of resources"
                    }
                ]
            }
        },
        {
            "name": "collection",
            "method": "GET",
            "path": "{endpoint}/collection/{id}/",
            "parameters": [
                {
                    "accept": "id",
                    "send": "id",
                    "required": true
                },
                {
                    "accept": "limit",
                    "send": "limit",
                    "required": false
                },
                {
                    "accept": "offset",
                    "send": "offset",
                    "required": false
                },
                {
                    "accept": "content_type",
                    "send": "content_type",
                    "required": false
                }
            ],
            "response": {
                "type": "json",
                "path": "",
                "parameters": [
                    {
                        "name": "id",
                        "path": "id"
                    },
                    {
                        "name": "url",
                        "path": "url"
                    },
                    {
                        "name": "name",
                        "path": "name"
                    },
                    {
                        "name": "count",
                        "path": "count"
                    },
                    {
                        "name": "next",
                        "path": "resources/next"
                    },
                    {
                        "name": "previous",
                        "path": "resources/previous"
                    },
                    {
                        "name": "subcollections",
                        "path": "subcollections",
                        "config": {
                            "path": "*",
                            "parameters": [
                                {
                                    "name": "name",
                                    "path": "name",
                                    "type": "text",
                                    "display": "Name"
                                },
                                {
                                    "name": "url",
                                    "path": "url",
                                    "type": "url",
                                    "display": "URL"
                                },
                                {
                                    "name": "uri",
                                    "path": "uri",
                                    "type": "url",
                                    "display": "URI"
                                },
                                {
                                    "name": "id",
                                    "path": "id",
                                    "type": "int",
                                    "display": "ID"
                                },
                                {
                                    "name": "description",
                                    "path": "description"
                                },
                                {
                                    "name": "public",
                                    "path": "public",
                                    "type": "bool",
                                    "display": "Public"
                                },
                                {
                                    "name": "size",
                                    "path": "size",
                                    "type": "int",
                                    "display": "Number of resources"
                                }
                            ]
                        }
                    },
                    {
                        "name": "resources",
                        "path": "resources/results",
                        "type": "object",
                        "config": {
                            "path": "*",
                            "parameters": [
                                {
                                    "name": "title",
                                    "path": "name",
                                    "type": "text",
                                    "display": "Name"
                                },
                                {
                                    "name": "content_types",
                                    "path": "content_types"
                                },
                                {
                                    "name": "url",
                                    "path": "url",
                                    "type": "url",
                                    "display": "URL"
                                },
                                {
                                    "name": "uri",
                                    "path": "uri",
                                    "type": "url",
                                    "display": "URI"
                                },
                                {
                                    "name": "id",
                                    "path": "id",
                                    "type": "int",
                                    "display": "ID"
                                },
                                {
                                    "name": "public",
                                    "path": "public",
                                    "type": "bool",
                                    "display": "Public"
                                }
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "content",
            "method": "GET",
            "path": "{endpoint}/content/{id}/",
            "parameters": [
                {
                    "accept": "id",
                    "send": "id",
                    "required": true
                }
            ],
            "response": {
                "type": "json",
                "path": "",
                "parameters": [
                    {
                        "name": "title",
                        "path": "name",
                        "type": "text",
                        "display": "Name"
                    },
                    {
                        "name": "next",
                        "path": "next/resource"
                    },
                    {
                        "name": "next_content",
                        "path": "next/content"
                    },
                    {
                        "name": "previous",
                        "path": "previous/resource"
                    },
                    {
                        "name": "previous_content",
                        "path": "previous/content"
                    },
                    {
                        "name": "url",
                        "path": "url",
                        "type": "url",
                        "display": "URL"
                    },
                    {
                        "name": "uri",
                        "path": "uri",
                        "type": "url",
                        "display": "URI"
                    },
                    {
                        "name": "id",
                        "path": "id",
                        "type": "int",
                        "display": "ID"
                    },
                    {
                        "name": "public",
                        "path": "public",
                        "type": "bool",
                        "display": "Public"
                    },
                    {
                        "name": "location",
                        "path": "content_location",
                        "type": "url",
                        "display": "Location"
                    },
                    {
                        "name": "content_type",
                        "path": "content_type",
                        "type": "text",
                        "display": "Content type"
                    }
                ]
            }
        },
        {
            "name": "resource",
            "method": "GET",
            "path": "{endpoint}/resource/{id}/",
            "parameters": [
                {
                    "accept": "id",
                    "send": "id",
                    "required": true
                }
            ],
            "response": {
                "type": "json",
                "path": "",
                "parameters": [
                    {
                        "name": "title",
                        "path": "name",
                        "type": "text",
                        "display": "Name"
                    },
                    {
                        "name": "url",
                        "path": "url",
                        "type": "url",
                        "display": "URL"
                    },
                    {
                        "name": "uri",
                        "path": "uri",
                        "type": "url",
                        "display": "URI"
                    },
                    {
                        "name": "id",
                        "path": "id",
                        "type": "int",
                        "display": "ID"
                    },
                    {
                        "name": "public",
                        "path": "public",
                        "type": "bool",
                        "display": "Public"
                    },
                    {
                        "name": "aggregate_content",
                        "path": "aggregate_content",
                        "type": "object",
                        "display": "Content",
                        "config": {
                            "path": "*",
                            "parameters": [
                                {
                                    "name": "content_type",
                                    "path": "content_type"
                                },
                                {
                                    "name": "resources",
                                    "path": "resources",
                                    "type": "object",
                                    "config": {
                                        "path": "*",
                                        "parameters": [
                                            {
                                                "name": "name",
                                                "path": "name",
                                                "type": "text",
                                                "display": "Name"
                                            },
                                            {
                                                "name": "location",
                                                "path": "content_location",
                                                "type": "url",
                                                "display": "Location"
                                            },
                                            {
                                                "name": "content_type",
                                                "path": "content_type",
                                                "type": "text",
                                                "display": "Content Type"
                                            },
                                            {
                                                "name": "id",
                                                "path": "id",
                                                "type": "int",
                                                "display": "ID"
                                            },
                                            {
                                                "name": "source",
                                                "path": "external_source",
                                                "type": "text",
                                                "display": "Source"
                                            },
                                            {
                                                "name": "content_for",
                                                "path": "content_for",
                                                "type": "int"
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "name": "parts",
                        "path": "parts",
                        "type": "object",
                        "display": "Parts",
                        "config": {
                            "path": "*",
                            "parameters": [
                                {
                                    "name": "id",
                                    "path": "source/id"
                                },
                                {
                                    "name": "uri",
                                    "path": "source/uri"
                                },
                                {
                                    "name": "content",
                                    "path": "source/content",
                                    "type": "object",
                                    "config": {
                                        "path": "*",
                                        "parameters": [
                                            {
                                                "name": "name",
                                                "path": "content_resource/name",
                                                "type": "text",
                                                "display": "Name"
                                            },
                                            {
                                                "name": "location",
                                                "path": "content_resource/content_location",
                                                "type": "url",
                                                "display": "Location"
                                            },
                                            {
                                                "name": "content_type",
                                                "path": "content_type",
                                                "type": "text",
                                                "display": "Content Type"
                                            },
                                            {
                                                "name": "id",
                                                "path": "content_resource/id",
                                                "type": "int",
                                                "display": "ID"
                                            },
                                            {
                                                "name": "source",
                                                "path": "content_resource/external_source",
                                                "type": "text",
                                                "display": "Source"
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "name": "content",
                        "path": "content",
                        "type": "object",
                        "config": {
                            "path": "*",
                            "parameters": [
                                {
                                    "name": "name",
                                    "path": "content_resource/name",
                                    "type": "text",
                                    "display": "Name"
                                },
                                {
                                    "name": "location",
                                    "path": "content_resource/content_location",
                                    "type": "url",
                                    "display": "Location"
                                },
                                {
                                    "name": "content_type",
                                    "path": "content_type",
                                    "type": "text",
                                    "display": "Content Type"
                                },
                                {
                                    "name": "id",
                                    "path": "content_resource/id",
                                    "type": "int",
                                    "display": "ID"
                                },
                                {
                                    "name": "source",
                                    "path": "content_resource/external_source",
                                    "type": "text",
                                    "display": "Source"
                                }
                            ]
                        }
                    }
                ]
            }
        }
    ]
}
"""