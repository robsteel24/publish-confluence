# Confluence Update Action

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/robsteel24/update-confluence/lint.yaml?branch=main)
![GitHub Release](https://img.shields.io/github/v/release/robsteel24/update-confluence)
![GitHub License](https://img.shields.io/github/license/robsteel24/update-confluence)

A GitHub Action for automatically updating version information on Confluence pages. This action is useful for keeping component versions up to date within Confluence tables based on specific environments.

## Features

- Updates a Confluence page’s table with specified version information for a component and environment.
- Utilises GitHub environment variables and secrets to securely handle credentials for Confluence.
- Can be triggered manually or within CI/CD workflows.

## Requirements

- A Confluence account with API access enabled.
- API token and base URL for your Confluence instance.
- A Confluence page ID where updates will be made.

## Usage

To use this action in a workflow, reference it within a GitHub Actions workflow file.

### Example Workflow

```yaml
name: Update Confluence Page

on:
  workflow_dispatch:
    inputs:
      environment:
        description: "The environment to update"
        required: true
        default: "DEV"
      component:
        description: "The component to update"
        required: true
        default: "cpt1"
      version:
        description: "The version number to set"
        required: true
        default: "2.3.4"

jobs:
  update-confluence:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Update Confluence Page
        uses: robsteel24/update-confluence@v1
        with:
          confluence_base_url: ${{ vars.CONFLUENCE_BASE_URL }}
          confluence_page_id: ${{ vars.CONFLUENCE_PAGE_ID }}
          atlassian_username: ${{ secrets.ATLASSIAN_USERNAME }}
          atlassian_api_token: ${{ secrets.ATLASSIAN_API_TOKEN }}
          component: ${{ github.event.inputs.component }}
          environment: ${{ github.event.inputs.environment }}
          version: ${{ github.event.inputs.version }}
