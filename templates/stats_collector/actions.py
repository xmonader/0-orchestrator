from js9 import j


def get_container(service, force=True):
    containers = service.producers.get('container')
    if not containers:
        if force:
            raise RuntimeError('Service didn\'t consume any containers')
        else:
            return
    return containers[0]


def init(job):
    from zeroos.orchestrator.configuration import get_configuration

    service = job.service
    container_actor = service.aysrepo.actorGet('container')
    config = get_configuration(service.aysrepo)

    args = {
        'node': service.model.data.node,
        'flist': config.get(
            '0-statscollector-flist', 'https://hub.gig.tech/gig-official-apps/0-statscollector-master.flist'),
        'hostname': service.model.data.node,
        'hostNetworking': True,
    }
    cont_service = container_actor.serviceCreate(instance='{}_stats_collector'.format(service.name), args=args)
    service.consume(cont_service)


def install(job):
    j.tools.async.wrappers.sync(job.service.executeAction('start', context=job.context))


def start(job):
    from zeroos.orchestrator.sal.Container import Container
    from zeroos.orchestrator.sal.stats_collector.stats_collector import StatsCollector

    service = job.service
    service.model.data.status = 'running'
    container = get_container(service)
    j.tools.async.wrappers.sync(container.executeAction('start', context=job.context))
    container_ays = Container.from_ays(container, job.context['token'], logger=service.logger)
    stats_collector = StatsCollector(
        container_ays, service.model.data.ip,
        service.model.data.port, service.model.data.db,
        service.model.data.retention, job.context['token'])
    stats_collector.start()

    service.saveAll()


def stop(job):
    from zeroos.orchestrator.sal.Container import Container
    from zeroos.orchestrator.sal.stats_collector.stats_collector import StatsCollector

    service = job.service
    service.model.data.status = 'halted'
    container = get_container(service)
    container_ays = Container.from_ays(container, job.context['token'], logger=service.logger)

    if container_ays.is_running():
        stats_collector = StatsCollector(
            container_ays, service.model.data.ip,
            service.model.data.port, service.model.data.db,
            service.model.data.retention, job.context['token'])
        stats_collector.stop()
        j.tools.async.wrappers.sync(container.executeAction('stop', context=job.context))
    job.service.saveAll()


def uninstall(job):
    container = get_container(job.service, False)
    if container:
        j.tools.async.wrappers.sync(container.executeAction('stop', context=job.context))
        j.tools.async.wrappers.sync(container.delete())
    j.tools.async.wrappers.sync(job.service.delete())


def processChange(job):
    from zeroos.orchestrator.sal.Container import Container
    from zeroos.orchestrator.sal.stats_collector.stats_collector import StatsCollector
    from zeroos.orchestrator.configuration import get_jwt_token_from_job

    service = job.service
    args = job.model.args

    if args.pop('changeCategory') != 'dataschema' or service.model.actionsState['install'] in ['new', 'scheduled']:
        return

    token = get_jwt_token_from_job(job)
    container = Container.from_ays(get_container(job.service), token, logger=service.logger)

    if args.get('ip'):
        service.model.data.ip = args['ip']
    if args.get('port'):
        service.model.data.port = args['port']
    if args.get('db'):
        service.model.data.db = args['db']
    if args.get('retention'):
        service.model.data.retention = args['retention']

    service.saveAll()
    stats_collector = StatsCollector(
        container, service.model.data.ip,
        service.model.data.port, service.model.data.db,
        service.model.data.retention, token)
    if container.is_running() and stats_collector.is_running():
        stats_collector.stop()
        stats_collector.start()


def init_actions_(service, args):
    return {
        'init': [],
        'install': ['init'],
        'monitor': ['start'],
        'delete': ['uninstall'],
        'uninstall': [],
    }


def monitor(job):
    import asyncio
    from zeroos.orchestrator.configuration import get_jwt_token
    from zeroos.orchestrator.sal.Container import Container
    from zeroos.orchestrator.sal.stats_collector.stats_collector import StatsCollector

    service = job.service
    token = get_jwt_token(service.aysrepo)

    container = get_container(service)
    container_ays = Container.from_ays(container, token)
    stats_collector = StatsCollector(
        container_ays, service.model.data.ip,
        service.model.data.port, service.model.data.db,
        service.model.data.retention, token)

    if service.model.data.status == 'running' and not stats_collector.is_running():
        loop = j.atyourservice.server.loop
        job.context['token'] = token
        asyncio.ensure_future(service.executeAction('start', context=job.context), loop=loop)

