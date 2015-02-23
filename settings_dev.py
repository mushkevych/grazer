settings = dict(
    # created with: sudo rabbitmqctl add_vhost /hadoop
    # set permissions with: sudo rabbitmqctl set_permissions -p /hadoop guest ".*" ".*" ".*"
    mq_host='rabbitmq.yourdomain.com',
    mq_user_id='MQ_USER',
    mq_password='MQ_PASSWORD',
    mq_vhost='/grazer',
    mq_port=5672,

    aws_redshift_host='REDSHIFT_HOST.redshift.amazonaws.com',
    aws_redshift_db='DB_NAME',
    aws_redshift_user='DB_USER',
    aws_redshift_password='DB_PASSWORD',
    aws_redshift_port=5439,

    mq_timeout_sec=10.0,
    aws_redshift_grazer_suffix='_test',
    csv_bulk_threshold=64,
)
