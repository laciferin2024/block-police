"""
ENS Resolution Tool

Provides tools for resolving and querying Ethereum Name Service (ENS) domains
using TheGraph ENS subgraph.
"""
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from typing import Dict, Any, Optional, List
import datetime
import os
from .registry import register_tool

from config import THEGRAPH_API_KEY


# GraphQL client setup
GRAPH_API_URL = "https://gateway.thegraph.com/api/subgraphs/id/5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH"

# Check if API key is available
if not THEGRAPH_API_KEY:
    print("Warning: THEGRAPH_API_KEY not found in environment variables")
    graphql_client = None
else:
    transport = AIOHTTPTransport(
        url=GRAPH_API_URL,
        headers={"Authorization": f"Bearer {THEGRAPH_API_KEY}"}
    )
    graphql_client = Client(transport=transport, fetch_schema_from_transport=False)


async def query_ens_domain(name: str) -> Optional[Dict[str, Any]]:
    """Query the ENS Subgraph for domain details."""
    if not graphql_client:
        return None

    query = gql("""
    query GetDomain($name: String!) {
        domains(where: { name: $name }) {
            id
            name
            labelName
            labelhash
            subdomainCount
            resolvedAddress {
                id
            }
            resolver {
                address
                addr {
                    id
                }
                contentHash
                texts
            }
            ttl
            isMigrated
            createdAt
            owner {
                id
            }
            registrant {
                id
            }
            wrappedOwner {
                id
            }
            expiryDate
            registration {
                registrationDate
                expiryDate
                cost
                registrant {
                    id
                }
                labelName
            }
            wrappedDomain {
                expiryDate
                fuses
                owner {
                    id
                }
                name
            }
        }
    }
    """)
    result = await graphql_client.execute_async(query, variable_values={"name": name})
    return result["domains"][0] if result["domains"] else None


async def query_domain_events(name: str) -> List[Dict[str, Any]]:
    """Query the ENS Subgraph for domain events."""
    if not graphql_client:
        return []

    query = gql("""
    query GetDomainEvents($name: String!) {
        domains(where: { name: $name }) {
            events {
                id
                __typename
                blockNumber
                transactionID
                ... on Transfer {
                    owner {
                        id
                    }
                }
                ... on NewOwner {
                    owner {
                        id
                    }
                    parentDomain {
                        name
                    }
                }
                ... on NewResolver {
                    resolver {
                        address
                        addr {
                            id
                        }
                    }
                }
                ... on NewTTL {
                    ttl
                }
                ... on WrappedTransfer {
                    owner {
                        id
                    }
                }
                ... on NameWrapped {
                    owner {
                        id
                    }
                    name
                    fuses
                    expiryDate
                }
                ... on NameUnwrapped {
                    owner {
                        id
                    }
                }
                ... on FusesSet {
                    fuses
                }
                ... on ExpiryExtended {
                    expiryDate
                }
            }
        }
    }
    """)
    result = await graphql_client.execute_async(query, variable_values={"name": name})
    return result["domains"][0]["events"] if result["domains"] and result["domains"][0]["events"] else []


@register_tool(
    name="ens_getAddress",
    description="Resolve an ENS name to its Ethereum address"
)
async def resolve_ens_name(domain: str) -> str:
    """
    Resolve an ENS name to its Ethereum address.

    Args:
        domain: The ENS domain name to resolve (e.g., "vitalik.eth")

    Returns:
        The resolved Ethereum address or error message
    """
    if not graphql_client:
        return "Error: TheGraph API key not configured"

    try:
        domain_data = await query_ens_domain(domain)
        if not domain_data:
            return f"No data found for ENS domain: {domain}"

        # Prefer resolvedAddress, fallback to resolver.addr
        address = (domain_data["resolvedAddress"]["id"] if domain_data["resolvedAddress"]
                else domain_data["resolver"]["addr"]["id"] if domain_data["resolver"] and domain_data["resolver"]["addr"]
                else "None")
        return address
    except Exception as e:
        return f"Error resolving ENS name: {str(e)}"


@register_tool(
    name="ens_getDomainDetails",
    description="Fetch detailed information for an ENS domain, including its address, owner, registration details, etc."
)
async def get_domain_details(domain: str) -> Dict[str, Any]:
    """
    Fetch detailed information for an ENS domain.

    Args:
        domain: The ENS domain name to query (e.g., "vitalik.eth")

    Returns:
        Dictionary containing detailed domain information
    """
    if not graphql_client:
        return {"error": "TheGraph API key not configured"}

    try:
        domain_data = await query_ens_domain(domain)
        if not domain_data:
            return {"error": f"No data found for ENS domain: {domain}"}

        # Extract and format domain data
        result = {
            "name": domain_data["name"],
            "address": "None",
            "owner": domain_data["owner"]["id"] if domain_data["owner"] else "None",
            "created": datetime.datetime.fromtimestamp(int(domain_data["createdAt"])).isoformat() if domain_data["createdAt"] else None,
            "expiry": datetime.datetime.fromtimestamp(int(domain_data["expiryDate"])).isoformat() if domain_data["expiryDate"] else None,
            "subdomainCount": domain_data["subdomainCount"],
            "registration": None,
            "resolver": None
        }

        # Get address
        if domain_data["resolvedAddress"]:
            result["address"] = domain_data["resolvedAddress"]["id"]
        elif domain_data["resolver"] and domain_data["resolver"]["addr"]:
            result["address"] = domain_data["resolver"]["addr"]["id"]

        # Registration details
        if domain_data["registration"]:
            result["registration"] = {
                "registrationDate": datetime.datetime.fromtimestamp(int(domain_data["registration"]["registrationDate"])).isoformat(),
                "expiryDate": datetime.datetime.fromtimestamp(int(domain_data["registration"]["expiryDate"])).isoformat(),
                "cost": domain_data["registration"]["cost"],
                "registrant": domain_data["registration"]["registrant"]["id"]
            }

        # Resolver details
        if domain_data["resolver"]:
            result["resolver"] = {
                "address": domain_data["resolver"]["address"],
                "contentHash": domain_data["resolver"]["contentHash"],
                "texts": domain_data["resolver"]["texts"]
            }

        return result
    except Exception as e:
        return {"error": f"Error getting domain details: {str(e)}"}


@register_tool(
    name="ens_getDomainEvents",
    description="Retrieve events associated with an ENS domain, such as transfers and resolver changes"
)
async def get_domain_events(domain: str) -> List[Dict[str, Any]]:
    """
    Retrieve events associated with an ENS domain.

    Args:
        domain: The ENS domain name to query events for (e.g., "vitalik.eth")

    Returns:
        List of domain events
    """
    if not graphql_client:
        return [{"error": "TheGraph API key not configured"}]

    try:
        events = await query_domain_events(domain)
        if not events:
            return [{"error": f"No events found for ENS domain: {domain}"}]

        formatted_events = []
        for event in events:
            event_type = event["__typename"]
            event_data = {
                "type": event_type,
                "blockNumber": event["blockNumber"],
                "transactionID": event["transactionID"]
            }

            # Add event-specific data
            if event_type == "Transfer":
                event_data["newOwner"] = event["owner"]["id"]
            elif event_type == "NewOwner":
                event_data["newOwner"] = event["owner"]["id"]
                event_data["parentDomain"] = event["parentDomain"]["name"]
            elif event_type == "NewResolver":
                event_data["resolverAddress"] = event["resolver"]["address"]
                if event["resolver"]["addr"]:
                    event_data["resolverAddr"] = event["resolver"]["addr"]["id"]
            elif event_type == "NewTTL":
                event_data["ttl"] = event["ttl"]
            elif event_type == "WrappedTransfer":
                event_data["newWrappedOwner"] = event["owner"]["id"]
            elif event_type == "NameWrapped":
                event_data["wrappedOwner"] = event["owner"]["id"]
                event_data["name"] = event["name"]
                event_data["fuses"] = event["fuses"]
                event_data["expiry"] = datetime.datetime.fromtimestamp(int(event["expiryDate"])).isoformat()
            elif event_type == "NameUnwrapped":
                event_data["owner"] = event["owner"]["id"]
            elif event_type == "FusesSet":
                event_data["fuses"] = event["fuses"]
            elif event_type == "ExpiryExtended":
                event_data["expiry"] = datetime.datetime.fromtimestamp(int(event["expiryDate"])).isoformat()

            formatted_events.append(event_data)

        return formatted_events
    except Exception as e:
        return [{"error": f"Error getting domain events: {str(e)}"}]


@register_tool(
    name="eth_resolveENS",
    description="Alternative method to resolve an ENS name to its address"
)
async def eth_resolve_ens(ensName: str) -> str:
    """
    Alternative method to resolve an ENS name to its address.
    Uses the same underlying implementation as ens_getAddress.

    Args:
        ensName: The ENS domain name to resolve (e.g., "vitalik.eth")

    Returns:
        The resolved Ethereum address or error message
    """
    return await resolve_ens_name(ensName)
