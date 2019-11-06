
$(aws ecr get-login --no-include-email --region us-east-1)
docker build -t rabbitmq_report .
docker tag rabbitmq_report:latest 481332135811.dkr.ecr.us-east-1.amazonaws.com/rabbitmq_report:latest
docker push 481332135811.dkr.ecr.us-east-1.amazonaws.com/rabbitmq_report:latest

aws ecs update-service --cluster knock_prod_ecs --service prod-rabbitmq-report --force-new-deployment --region us-east-1 >> deploy.log

aws ecs wait services-stable --cluster knock_prod_ecs --service prod-rabbitmq-report --region us-east-1
