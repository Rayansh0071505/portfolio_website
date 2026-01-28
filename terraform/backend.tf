terraform {
  backend "s3" {
    bucket  = "rayansh-portfolio-tf-state-99f29c67"
    key     = "infrastructure.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
