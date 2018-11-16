from boa.interop.System.Storage import *
from boa.interop.System.ExecutionEngine import *
from boa.interop.System.Runtime import *
from boa.interop.System.Blockchain import GetHeight, GetHeader, GetBlock
from boa.interop.System.Header import GetHash
from boa.interop.Ontology.Native import *
from boa.builtins import state, sha256, concat, ToScriptHash

#ONG for now, needs to be changed to ZPT then
contractAddress = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02')

ctx = GetContext()
selfAddr = GetExecutingScriptHash()

# constants

node_state_idle = 0;
node_state_applied = 1;
node_state_running = 2;
node_state_shutdown = 3;


factor8 = 1000000000; # = 1 ONG/ZPT
minNodeCapacity = 1000000 * 1000000000; # = 1 ONG/ZPT


NODE_PREFIX = 'NODE';
ADMIN_PREFIX = 'ADMIN'; 
MEMBER_PREFIX = 'MEMBER';

def Main(operation, args):
    if operation == 'createNode':
        if len(args) == 4:
            admin = args[0]; # node creator 
            minAmount = args[1]; # integer min ZPT per participant
            nodeFee = args[2]; # integer 100 = 1%
            nodeDuration = args[3]; # integer / months ? weeks
            return createNode(admin, minAmount, nodeFee, nodeDuration);
    if operation == 'deposit':
        if len(args) == 3:
            node_id = args[0]; # node to deposit to
            amount = args[1]; # integer ZPT 
            address = args[2]; # ZPT address
            return deposit(node_id, amount, address);
    if operation == 'withdraw':
        if len(args) == 3:
            node_id = args[0]; # node to deposit to
            amount = args[1]; # integer ZPT 
            address = args[2]; # ZPT address
            return withdraw(node_id, amount, address);
    if operation == 'addNodeAdmin':
        return addNodeAdmin(args[0], args[1]);
    if operation == 'removeNodeAdmin':
        return removeNodeAdmin(args[0], args[1]);
    if operation == 'getNodeInfo':
        if len(args) == 2:
            return getNodeInfo(args[0], args[1]);
    if operation == 'getMemberInfo':
        if len(args) == 3:
            return getNodeInfo(args[0], args[1], args[2]);
    if operation == 'getName':
        return getName()
    if operation == 'test':
        acct = args[0];
        return test(acct);

    return False
    
def test(acct):
    rr = CheckWitness(acct);
    Notify(['1', rr]);
    return True;
    

def createNode(admin, minAmount, nodeFee, nodeDuration):
    members = [];
    admins = [admin]; # list of admins
    node_id = concatKey(NODE_PREFIX, getRandom());
    amount = 0;
    node = {'id': node_id, 
            'fee': nodeFee, 
            'amount': amount, 
            'duration': nodeDuration, 
            'state': 0,
            'admins': admins,
            'members': members
            };
    return putNode(node);

def addNodeAdmin(node_id, admin):
    node = getNode(node_id);
    admins = node['admins'];
    if not getAdmin(admin):
        putAdmin(admin, node_id);
        admins.append(admin);
        node['admins'] = admins;
        return putNode(node);

def removeNodeAdmin(node_id, admin):
    node = getNode(node_id);
    admins = node['admins'];
    if getAdmin(admin):
        Delete(ctx, admin);
        del admins[admin];
        return putNode(node);    

def modifyNodeMember(node_id, address, amount, deposit):
    node = getNode(node_id);
    members = node['members'];
    t_amount = 0;
    if deposit:
        if getMember(address):
            m_amount = getMember(address);
            t_amount = m_amount + amount;
            putMember(address, t_amount);
        else:
            putMember(address, amount);
            t_amount = amount;
            members.append = address;
            node['members'] = members;

    else:
        if getMember(address):
            m_amount = getMember(address);
            if m_amount < amount:
                return False;
            t_amount = m_amount - amount;
            putMember(address, t_amount);
    current_t_amount = node['amount'];
    node['amount'] = current_t_amount + t_amount;
    return putNode(node);
    
def putAdmin(admin, node):
    a_key = concatKey(ADMIN_PREFIX, admin);
    Put(ctx, a_key, node);
    if (Get(ctx, a_key)):
        Notify(['admin', a_key, node]);
        return True;
    return False;

def getAdmin(admin):
    a_key = concatKey(ADMIN_PREFIX, admin);
    return Get(ctx, a_key);
    
def removeAdmin(admin):
    a_key = concatKey(ADMIN_PREFIX, admin);
    return Delete(ctx, a_key);
    
def putMember(member, amount):
    m_key = concatKey(MEMBER_PREFIX, member);
    Put(ctx, m_key, amount);
    if (Get(ctx, m_key)):
        Notify(['member_id', m_key, amount]);
        return True;
    return False;

def getMember(member):
    m_key = concatKey(MEMBER_PREFIX, member);
    return Get(ctx, m_key);

def removeMember(member):
    m_key = concatKey(MEMBER_PREFIX, member);
    return Delete(ctx, m_key);
    
def putNode(node):
    Put(ctx, node['id'], Serialize(node));
    if (Get(ctx, node['id'])):
        Notify(['node_id', node['id']])
        return True;
    return False;

def getNode(node_id):
    ser_node = Get(ctx, node_id);
    node = Deserialize(ser_node);
    return node;

def getNodeInfo(node_id, info):
    ser_node = Get(ctx, node_id);
    if (ser_node):
        node = Deserialize(ser_node);
        Notify(['test', node[info]])
        return node[info];
        
def getMemberInfo(node_id, address, info):
    ser_node = Get(ctx, node_id);
    if (ser_node):
        node = Deserialize(ser_node);
        members = node['members'];
        for member in members:
            if member['address'] == address:
                Notify(['test', member[info]])
                return member[info];

def deposit(node_id, amount, address):
    if CheckWitness(address):
        Notify(['AMOUNT', amount, amount * factor8]);
        c_amount = amount * factor8;
        if depositZPT(address, selfAddr, c_amount):
            Notify(["Deposited"]);
            #update node
            if modifyNodeMember(node_id, address, c_amount, True):
                Notify(["Added"]);
                return True;
        else:
            Notify(["transfer ong failed!"]);
            return False;
    else:
        Notify(["CheckWitness failed!"]);
        return False;

def withdraw(node_id, amount, address):
    if CheckWitness(address):
        c_amount = amount * factor8;
        if withdrawZPT(address, c_amount):
            #update node
            modifyNodeMember(node_id, address, c_amount, False);
            Notify(["Removed"]);
            return True;
        else:
            Notify(["transfer ong failed!"]);
            return False;
    else:
        Notify(["CheckWitness failed!"]);
        return False;


def depositZPT(fromacct, toacct, amount):
    if CheckWitness(fromacct):
        param = makeState(fromacct, toacct, amount);
        res = Invoke(0, contractAddress, 'transfer', [param]);
        Notify(res);
        if res and res == b'\x01':
            Notify(['transfer succeed']);
            return True;
        else:
            Notify(['transfer failed']);
            return False;
    else:
        Notify(['checkWitness failed']);
        return False;


def withdrawZPT(toacct, amount):
    param = makeState(selfAddr, toacct, amount);
    res = Invoke(1, contractAddress, 'transfer', [param]);
    Notify(res);
    if res and res == b'\x01':
        Notify(['transfer succeed']);
        return True;
    else:
        Notify(['transfer failed']);

        return False;

def concatKey(str1,str2):
    return concat(concat(str1, '_'), str2);


def makeState(fromacct, toacct, amount):
    return state(fromacct, toacct, amount);


def getTimestamp():
    timestamp = GetTime();
    return timestamp;


def getRandom():
    time = GetTime();
    height = GetHeight();
    header = GetHeader(height);
    tmp = sha256(abs(GetHash(header)) % time);
    return tmp;

def getName():
    Notify('ZPT-Node-Contract')
    return 'ZPT-Node-Contract';
