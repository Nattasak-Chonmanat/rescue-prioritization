resource "aws_dynamodb_table" "prioritization_records" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "request_id"
  range_key      = "incident_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  attribute {
    name = "incident_id"
    type = "S"
  }

  # Global secondary index for querying by incident_id
  global_secondary_index {
    name            = "incident_id-index"
    hash_key        = "incident_id"
    projection_type = "ALL"
  }

  # Global secondary index for querying by status
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    projection_type = "ALL"
  }

  attribute {
    name = "status"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  ttl {
    attribute_name = "expiration_time"
    enabled        = true
  }

  tags = {
    Name = "prioritization-records-table"
  }
}
