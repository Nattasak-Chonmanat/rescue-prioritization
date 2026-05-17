resource "aws_pipes_pipe" "prioritize_pipe" {
  name     = "PrioritizePipe"
  role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/LabRole"

  source = aws_sqs_queue.rescue_request_created_queue.arn
  target = aws_sfn_state_machine.prioritization_state_machine.arn

  target_parameters {
    step_function_state_machine_parameters {
      invocation_type = "FIRE_AND_FORGET"
    }
  }

  depends_on = [
    aws_sqs_queue.rescue_request_created_queue,
    aws_sfn_state_machine.prioritization_state_machine,
  ]

  tags = {
    Name = "PrioritizePipe"
  }
}
