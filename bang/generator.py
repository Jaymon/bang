
class Post(object):
    def __init__(self, directory):
        self.directory = directory

    def __str__(self):
        return self.directory.path


class Aux(object):
    def __init__(self, directory):
        self.directory = directory

    def __str__(self):
        return self.directory.path


class Site(object):
    def __init__(self, project_dir, output_dir):
        self.project_dir = project_dir
        self.output_dir = output_dir

    def output(self):
        #pout.v(self.project_dir, self.output_dir)
        self.output_dir.clear()
        posts = []
        auxs = []
        for d in self.project_dir.input_dir:
            if d.is_aux():
                auxs.append(Aux(d))

            elif d.is_post():
                posts.append(Post(d))

        pout.v(posts, auxs)
