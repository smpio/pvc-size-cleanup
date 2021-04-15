import kubernetes
import googleapiclient.errors
import googleapiclient.discovery


class Main():
    def main(self):
        compute = googleapiclient.discovery.build('compute', 'v1')
        disks = compute.disks().list(
            project='smp-io',
            zone='europe-west1-b',
        ).execute()['items']
        self.disk_map = {d['name']: d for d in disks}

        configuration = kubernetes.client.Configuration()
        configuration.host = 'http://127.0.0.1:8001'
        kubernetes.client.Configuration.set_default(configuration)

        v1 = kubernetes.client.CoreV1Api()
        pvs = v1.list_persistent_volume().items

        for pv in pvs:
            self.do_pv(pv)

        for disk_name in self.disk_map.keys():
            print('Disk left', disk_name)

    def do_pv(self, pv):
        disk_name = pv.spec.gce_persistent_disk.pd_name
        try:
            disk = self.disk_map[disk_name]
        except KeyError:
            print('No disk for PV', pv.metadata.name)
            return

        try:
            pv_size = pv.spec.capacity['storage']
            if not pv_size.endswith('Gi'):
                print('Unknown PV size', pv.metadata.name, pv_size)
                return
            pv_size = int(pv_size[:-2])
            disk_size = int(disk['sizeGb'])

            if pv_size != disk_size:
                print(
                    'Different size',
                    pv.metadata.name,
                    pv_size, '->', disk_size,
                    pv.spec.claim_ref.namespace, '/', pv.spec.claim_ref.name,
                )
                return
        finally:
            self.disk_map.pop(disk_name)


if __name__ == '__main__':
    Main().main()
