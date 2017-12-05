from troposphere import Ref, Base64, Join, Tags, GetAtt, Select, Template, Parameter, Output
from troposphere.cloudformation import Metadata, Init, InitConfig, Authentication, AuthenticationBlock
from troposphere.ec2 import EIP, SecurityGroup, SecurityGroupRule, NetworkInterfaceProperty, Instance


def generate_template():

    template = Template()

    ref_stack_id = Ref('AWS::StackId')
    ref_region = Ref('AWS::Region')
    ref_stack_name = Ref('AWS::StackName')

    template.add_description(
        'Counter Strike Source Dedicated Server instances Stack implementing a linux ' +
        'server and installing the dedicated server on it'
    )

    aws_access_key = template.add_parameter(Parameter(
        'AWSAccessKey',
        Type='String',
        Description='AWS Access Key'
    ))

    aws_secret_key = template.add_parameter(Parameter(
        'AWSSecretKey',
        Type='String',
        Description='AWS Secret Key'
    ))

    css_instance_name = template.add_parameter(Parameter(
        'CSSInstanceName',
        Default='css-server',
        Type='String',
        Description='The Name tag for the CSS Server instance.'
    ))

    ami_id_linux = template.add_parameter(Parameter(
        'AmiIdLinux',
        Default='ami-82f4dae7',
        Type='AWS::EC2::Image::Id',
        Description='Instances in the DMZ will use this AMI.'
    ))

    instance_type = template.add_parameter(Parameter(
        'InstanceType',
        Type='String',
        Description='Instances launched will use this EC2 Instance type.',
        AllowedValues=[
            't2.nano', 't2.micro', 't2.small', 't2.medium',
            'c3.large', 'c3.xlarge', 'c3.2xlarge',
            'c4.large', 'c4.xlarge', 'c4.2xlarge', 'm4.large'
        ],
        ConstraintDescription='must be a supported EC2 Instance type'
    ))

    vpc_id = template.add_parameter(Parameter(
        'VPCId',
        Type='String',
    ))

    public_subnet = template.add_parameter(Parameter(
        'PublicSubnet',
        Type='String',
    ))

    private_subnet = template.add_parameter(Parameter(
        'PrivateSubnet',
        Type='String',
    ))

    iam_role = template.add_parameter(Parameter(
        'IAMRole',
        Type='String',
        Description='The IAM role associated with the instances.'
    ))

    keyname = template.add_parameter(Parameter(
        'KeyName',
        Type='AWS::EC2::KeyPair::KeyName',
        Description='Instances in the Auto Scaling Group will use this ssh key.'
    ))

    css_init_config_script = template.add_parameter(Parameter(
        "CSSInitConfigScript",
        Type="String",
        Description="File containing initial configuration script"
    ))

    css_install_script = template.add_parameter(Parameter(
        "CSSInstallScript",
        Type="String",
        Description="File containing installation script for CSS server"
    ))

    css_mods_tgz = template.add_parameter(Parameter(
        "CSSModsTgz",
        Type="String",
        Description="File containing mods of the CSS server"
    ))

    css_mapcycle_txt = template.add_parameter(Parameter(
        "CSSMapcycleTxt",
        Type="String",
        Description="mapcycle.txt of the CSS server"
    ))

    css_server_cfg = template.add_parameter(Parameter(
        "CSSServerCfg",
        Type="String",
        Description="server.cfg of the CSS server"
    ))

    css_rcon_password = template.add_parameter(Parameter(
        "CSSRconPassword",
        Type="String",
        Description="RCON password of the CSS server"
    ))

    bucket_name = template.add_parameter(Parameter(
        "BucketName",
        Type="String",
        Description="Name of the S3 Bucket"
    ))

    # Create Security Groups

    sshlocation_param = template.add_parameter(
        Parameter(
            'SSHLocation',
            Description=' The IP address range that can be used to SSH to the EC2 instances',
            Type='String',
            MinLength='9',
            MaxLength='18',
            Default='0.0.0.0/0',
            AllowedPattern="(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})",
            ConstraintDescription=(
                "must be a valid IP CIDR range of the form x.x.x.x/x."),
        ))

    public_security_group = template.add_resource(
        SecurityGroup(
            'PublicSecurityGroup',
            GroupDescription='Security group for instances in the DMZ',
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol='icmp',
                    FromPort='8',
                    ToPort='-1',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='22',
                    ToPort='22',
                    CidrIp=Ref(sshlocation_param)),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='1200',
                    ToPort='1200',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='udp',
                    FromPort='1200',
                    ToPort='1200',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='udp',
                    FromPort='27005',
                    ToPort='27005',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='27015',
                    ToPort='27015',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='udp',
                    FromPort='27015',
                    ToPort='27015',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='udp',
                    FromPort='27020',
                    ToPort='27020',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='udp',
                    FromPort='26901',
                    ToPort='26901',
                    CidrIp='0.0.0.0/0')],
            SecurityGroupEgress=[
                SecurityGroupRule(
                    IpProtocol='icmp',
                    FromPort='8',
                    ToPort='-1',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='80',
                    ToPort='80',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='443',
                    ToPort='443',
                    CidrIp='0.0.0.0/0')],
            VpcId=Ref(vpc_id),
        ))

    private_security_group = template.add_resource(
        SecurityGroup(
            'PrivateSecurityGroup',
            GroupDescription='Security group for instances in the private subnet(s)',
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol='icmp',
                    FromPort='8',
                    ToPort='-1',
                    CidrIp='0.0.0.0/0')],
            SecurityGroupEgress=[
                SecurityGroupRule(
                    IpProtocol='icmp',
                    FromPort='8',
                    ToPort='-1',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='80',
                    ToPort='80',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='443',
                    ToPort='443',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='53',
                    ToPort='53',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='udp',
                    FromPort='53',
                    ToPort='53',
                    CidrIp='0.0.0.0/0'),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='0',
                    ToPort='65535',
                    SourceSecurityGroupId=Ref(public_security_group)),
                SecurityGroupRule(
                    IpProtocol='udp',
                    FromPort='0',
                    ToPort='65535',
                    SourceSecurityGroupId=Ref(public_security_group))],
            VpcId=Ref(vpc_id),
        ))

    # Create CSS Server instance in the public subnet
    css_server_instance = template.add_resource(
        Instance(
            'CSSServerInstance',
            ImageId=Ref(ami_id_linux),
            InstanceType=Ref(instance_type),
            KeyName=Ref(keyname),
            IamInstanceProfile=Ref(iam_role),
            NetworkInterfaces=[
                NetworkInterfaceProperty(
                    GroupSet=[
                        Ref(public_security_group)],
                    AssociatePublicIpAddress='false',
                    DeviceIndex='0',
                    DeleteOnTermination='true',
                    SubnetId=Ref(public_subnet))],
            Tags=Tags(
                Name=Ref(css_instance_name),
                Application=ref_stack_id),
            UserData=Base64(
                Join('', [
                    '#!/bin/bash -xe\n',
                    'curl https://bootstrap.pypa.io/get-pip.py | python\n',
                    'pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz\n',
                    '/usr/local/bin/cfn-init -v ',
                    '         --stack ',
                    ref_stack_name,
                    '         --resource CSSServerInstance ',
                    '         --region ',
                    ref_region,
                    '\n'])),
            Metadata=Metadata(
                Authentication({
                    "S3AccessCreds": AuthenticationBlock(
                        type="S3",
                        accessKeyId=Ref(aws_access_key),
                        secretKey=Ref(aws_secret_key),
                        buckets=Ref(bucket_name)
                    )
                }),
                Init({
                    "config": InitConfig(
                        sources={
                            '/tmp/mods': Ref(css_mods_tgz),
                        },
                        files={
                            '/tmp/init-config.sh': {
                                'source': Ref(css_init_config_script),
                                'authentication': 'S3AccessCreds',
                                'mode': '000755',
                                'owner': 'root',
                                'group': 'root'
                            },
                            '/tmp/css-install-script.sh': {
                                'source': Ref(css_install_script),
                                'authentication': 'S3AccessCreds',
                                'mode': '000755',
                                'owner': 'root',
                                'group': 'root'
                            },
                            '/tmp/cfg/mapcycle.txt': {
                                'source': Ref(css_mapcycle_txt),
                                'authentication': 'S3AccessCreds'
                            },
                            '/tmp/cfg/server.cfg': {
                                'source': Ref(css_server_cfg),
                                'authentication': 'S3AccessCreds'
                            }
                        },
                        commands={
                            # '1_set_chmod': {
                            #     'command': 'chmod 755 /tmp/*.sh',
                            #     'cwd': '~',
                            # },
                            '2_run_init-config.sh': {
                                'command': '/tmp/init-config.sh',
                                'cwd': '~',
                                'env': { 'RCON_PASSWORD': Ref(css_rcon_password) }
                            }
                        },
                    )
                })
            )
        ))

    css_server_instance_ip_address = template.add_resource(
        EIP('IPAddress',
            Domain='vpc',
            InstanceId=Ref(css_server_instance)
            ))

    template.add_output(Output(
        'InstanceIp',
        Value=Ref(css_server_instance_ip_address),
        Description='Linux Instance IP',
    ))

    return template

if __name__ == '__main__':
    print (generate_template().to_json())