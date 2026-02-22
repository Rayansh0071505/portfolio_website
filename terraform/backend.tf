terraform {
  backend "s3" {
    bucket  = "rayansh-portfolio-tf-state-1a69217f"
    key     = "infrastructure.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
