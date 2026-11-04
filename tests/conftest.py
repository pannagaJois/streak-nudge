"""Global test configuration and mocked AWS credentials."""

import os
import pytest

# Ensure mocked AWS credentials are fixed for moto
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
os.environ["AWS_REGION"] = "ap-south-1"
