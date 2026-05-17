resource "aws_dynamodb_table" "prioritization_records" {
  name         = "prioritization_records"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"
  range_key    = "incident_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  attribute {
    name = "incident_id"
    type = "S"
  }

  global_secondary_index {
    name            = "incident_id-index"
    hash_key        = "incident_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "prioritization_records"
  }
}
