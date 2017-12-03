from troposphere import Template, Parameter, Ref, Base64, Join, Tags, GetAtt, Output, Select
from troposphere.ec2 import VPC, Subnet, NatGateway, InternetGateway, RouteTable, Route, VPCGatewayAttachment, \
    SubnetRouteTableAssociation, EIP, SecurityGroup, SecurityGroupRule, NetworkInterfaceProperty, Instance, NetworkAcl, \
    NetworkAclEntry, PortRange, SubnetNetworkAclAssociation, Tag


def generate_template():
    template = Template()

    ref_stack_id = Ref('AWS::StackId')
    ref_region = Ref('AWS::Region')
    ref_stack_name = Ref('AWS::StackName')

    template.add_description(
        'Base infrastructure Stack implementing VPC Scenario 2 with 2 private subnets'
    )

    environment_name = template.add_parameter(Parameter(
        'EnvName',
        Type='String',
        Description='The name of the environment being deployed.'
    ))

    aws_region = template.add_parameter(Parameter(
        'AWSRegion',
        Type='String',
        Description='The name of the region the environment should be deployed.'
    ))

    # Create VPC

    vpc = template.add_resource(
        VPC(
            'VPC',
            CidrBlock='10.0.0.0/16',
            EnableDnsHostnames=True,
            Tags=Tags(
                Application=ref_stack_id)))

    internet_gateway = template.add_resource(
        InternetGateway(
            'InternetGateway',
            Tags=Tags(
                Application=ref_stack_id)))

    internet_gateway_attachment = template.add_resource(
        VPCGatewayAttachment(
            'AttachGateway',
            VpcId=Ref(vpc),
            InternetGatewayId=Ref(internet_gateway)))

    # Create Routing Tables
    public_route_table = template.add_resource(
        RouteTable(
            'PublicRouteTable',
            VpcId=Ref(vpc),
            Tags=Tags(
                Application=ref_stack_id)))

    route = template.add_resource(
        Route(
            'Route',
            DependsOn='AttachGateway',
            GatewayId=Ref('InternetGateway'),
            DestinationCidrBlock='0.0.0.0/0',
            RouteTableId=Ref(public_route_table),
        ))

    # Create NAT Gateway for Public Subnet

    nat_eip1 = template.add_resource(EIP(
        'NatEip1',
        Domain="vpc",
    ))

    nat_eip2 = template.add_resource(EIP(
        'NatEip',
        Domain="vpc",
    ))

    # Create Public Subnet
    public_subnet1 = template.add_resource(
        Subnet(
            'PublicSubnet1',
            CidrBlock='10.0.0.0/24',
            AvailabilityZone=Join("", [Ref(aws_region), 'a']),
            MapPublicIpOnLaunch=True,
            VpcId=Ref(vpc),
            Tags=Tags(
                Name='public-10.0.0.0',
                Application=ref_stack_id)))

    public_subnet2 = template.add_resource(
        Subnet(
            'PublicSubnet2',
            CidrBlock='10.0.3.0/24',
            AvailabilityZone=Join("", [Ref(aws_region), 'b']),
            MapPublicIpOnLaunch=True,
            VpcId=Ref(vpc),
            Tags=Tags(
                Name='public-10.0.3.0',
                Application=ref_stack_id)))

    subnetRouteTableAssociation1 = template.add_resource(
        SubnetRouteTableAssociation(
            'SubnetRouteTableAssociation1',
            SubnetId=Ref(public_subnet1),
            RouteTableId=Ref(public_route_table),
        ))

    subnetRouteTableAssociation2 = template.add_resource(
        SubnetRouteTableAssociation(
            'SubnetRouteTableAssociation2',
            SubnetId=Ref(public_subnet2),
            RouteTableId=Ref(public_route_table),
        ))

    nat1 = template.add_resource(NatGateway(
        'Nat1',
        AllocationId=GetAtt(nat_eip1, 'AllocationId'),
        SubnetId=Ref(public_subnet1),
    ))

    nat2 = template.add_resource(NatGateway(
        'Nat2',
        AllocationId=GetAtt(nat_eip2, 'AllocationId'),
        SubnetId=Ref(public_subnet2),
    ))

    private_subnet1 = template.add_resource(
        Subnet(
            'PrivateSubnet1',
            CidrBlock='10.0.1.0/24',
            AvailabilityZone=Join("", [Ref(aws_region), 'a']),
            MapPublicIpOnLaunch=False,
            VpcId=Ref(vpc),
            Tags=Tags(
                Name='private-az1-10.0.1.0',
                Application=ref_stack_id)))

    private_subnet2 = template.add_resource(
        Subnet(
            'PrivateSubnet2',
            CidrBlock='10.0.2.0/24',
            AvailabilityZone=Join("", [Ref(aws_region), 'b']),
            MapPublicIpOnLaunch=False,
            VpcId=Ref(vpc),
            Tags=Tags(
                Name='private-az2-10.0.2.0',
                Application=ref_stack_id)))

    private_route_table1 = template.add_resource(
        RouteTable(
            'PrivateRouteTable1',
            VpcId=Ref(vpc),
            Tags=Tags(
                Application=ref_stack_id)))

    private_route_table2 = template.add_resource(
        RouteTable(
            'PrivateRouteTable2',
            VpcId=Ref(vpc),
            Tags=Tags(
                Application=ref_stack_id)))

    template.add_resource(
        Route(
            'NatRoute1',
            RouteTableId=Ref(private_route_table1),
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=Ref(nat1), ))

    template.add_resource(
        Route(
            'NatRoute2',
            RouteTableId=Ref(private_route_table2),
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=Ref(nat2), ))

    template.add_resource(
        SubnetRouteTableAssociation(
            'PrivateSubnetRouteTableAssociation1',
            SubnetId=Ref(private_subnet1),
            RouteTableId=Ref(private_route_table1), ))

    template.add_resource(
        SubnetRouteTableAssociation(
            'PrivateSubnetRouteTableAssociation2',
            SubnetId=Ref(private_subnet2),
            RouteTableId=Ref(private_route_table2), ))

    # Outputs

    template.add_output(Output(
        'VPCId',
        Value=Ref(vpc),
        Description='VPC Id'
    ))

    template.add_output(Output(
        'PublicSubnet1',
        Value=Ref(public_subnet1),
        Description='Public subnet ID'
    ))

    template.add_output(Output(
        'PublicSubnet2',
        Value=Ref(public_subnet2),
        Description='Public subnet ID'
    ))

    template.add_output(Output(
        'PrivateSubnet1',
        Value=Ref(private_subnet1),
        Description='Private subnet ID'
    ))

    template.add_output(Output(
        'PrivateSubnet2',
        Value=Ref(private_subnet2),
        Description='Private subnet ID'
    ))

    template.add_output(Output(
        'StackID',
        Value=Ref('AWS::StackName'),
        Description='Stack ID'
    ))

    return template

if __name__ == '__main__':
    print (generate_template().to_json())