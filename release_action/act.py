# coding=utf-8
from core.common import get_result, logger, try_except
from release.models import Type, Mission_control, Progress, Type_step, Step, Mission
from play.tasks import ProgressHostRunTask, CmdRunTask, VersionConfirmTask, PublishTask


class ProgressActAdmin(object):
    @staticmethod
    @try_except
    def __do_task(task_cls, *args, **kwargs):
        task_cls().delay(*args, **kwargs)
        return get_result(0, 'add to queue')

    def progress_run(self, mission_id, host, status):
        return self.__do_task(ProgressHostRunTask, get_result(0, ''), Mission.objects.get(mark=mission_id), host, status)

    def progress_one(self, mission_id, host, order):
        return self.__do_task(CmdRunTask, mission_id, host, order)


def mission_exec_status(exec_id, content):
    if content in ('times', 'host_done'):
        mission_control = Mission_control.objects.get(id=exec_id)
        if content == 'times':
            mission_control.times += 1
        else:
            mission_control.host_done += 1
        mission_control.save()
        result = get_result(0, 'done')
    else:
        logger.error('%s', 'no this field')
        result = get_result(1, 'no this field')
    return result


def mission_version_confirm(mission_id):
    return VersionConfirmTask().run(mission_id)


def format_act(m):
    n_act = {}
    n = tuple(eval(m['args']))
    mission, a, b = n
    n_act['mission'] = mission
    n_act['func'] = m['name']
    n_act['id'] = m['id']
    return n_act


@try_except
def mission_cancel(mission_id):
    from ops.celery import app
    while 1:
        reserved_act = app.control.inspect().reserved()
        all_acts = [format_act(m) for m in reserved_act['celery@Ops_Dev']]
        revoke_list = [x['id'] for x in all_acts if x['mission'] == mission_id]
        if len(revoke_list) == 0:
            break
        else:
            for n in revoke_list:
                app.control.revoke(n)
    return get_result(0, 'done')


def workflow_get(id=0):
    """
    get the workflow-info
    :param id:
    :return:
    """

    def work_order(node):
        return node['order']

    if id == 0:
        result = []
        all_type = Type.objects.all()
        for m in all_type:
            t_result = {'id': m.id, 'type': m.alias,}
            node_results = []
            for n in Type_step.objects.filter(type=m):
                n_result = {'alias': n.step.alias, 'order': n.order}
                node_results.append(n_result)
            t_result['step'] = sorted(node_results, key=work_order)
            result.append(t_result)
    else:
        n_type = Type.objects.get(id=id)
        result = {'id': id, 'type': n_type.alias}
        node_results = []
        for n in Type_step.objects.filter(type=n_type):
            n_result = {'alias': n.step.alias, 'order': n.order}
            node_results.append(n_result)
        result['step'] = sorted(node_results, key=work_order)
    return result


@try_except
def workflow_update(new_data):
    type_id = new_data['id']
    n_type = Type.objects.get(id=type_id)
    Type_step.objects.filter(type=n_type).delete()
    for m in new_data['step']:
        Type_step.objects.create(
            type=n_type,
            step=Step.objects.get(alias=m['alias']),
            order=m['order']
        )
    return get_result(0, 'done!')
