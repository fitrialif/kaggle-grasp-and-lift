from lasagne import layers
from lasagne import nonlinearities
from lasagne import init
#from lasagne.layers import cuda_convnet
from lasagne.layers import conv
from lasagne.layers import pool

#Conv1DLayer = cuda_convnet.Conv1DCCLayer
#MaxPool1DLayer = cuda_convnet.MaxPool1DCCLayer

Conv1DLayer = conv.Conv1DLayer
MaxPool1DLayer = pool.MaxPool1DLayer


class SubsampleLayer(layers.Layer):
    def __init__(self, incoming, window, name=None, **kwargs):
        super(SubsampleLayer, self).__init__(incoming, **kwargs)
        if not isinstance(window, slice):
            self.window = slice(*window)
        else:
            self.window = window

    def get_output_shape_for(self, input_shape):
        output_shape = list(input_shape)
        if self.window.stop is None and self.window.start is None:
            output_shape[2] = input_shape[2] / self.window.step
        elif self.window.stop is None:
            output_shape[2] = (input_shape[2] - self.window.start) / self.window.step
        elif self.window.start is None:
            output_shape[2] = self.window.stop / self.window.step
        else:
            output_shape[2] = (self.window.stop - self.window.start) / self.window.step
        return tuple(output_shape)

    def get_output_for(self, input, **kwargs):
        step = self.window.step
        start = (input.shape[0] - 1) % step
        if self.window.start is not None:
            start += self.window.start
        stop = self.window.stop

        s = slice(start, stop, step)
        return input[:, :, s]


def build_model(batch_size,
                num_channels,
                input_length,
                output_dim,):
    l_in = layers.InputLayer(
        shape=(batch_size, num_channels, input_length),
        name='input',
    )

    l_ss_left = SubsampleLayer(
        l_in,
        window=(None, None, 10),
        name='l_ss_left',
    )

    l_ss_right = SubsampleLayer(
        l_in,
        window=(1000, None, 5),
        name='l_ss_right',
    )

    l_conv1_left = Conv1DLayer(
        l_ss_left,
        name='conv1_left',
        num_filters=8,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_conv1_right = Conv1DLayer(
        l_ss_right,
        name='conv1_right',
        num_filters=8,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_pool1_left = MaxPool1DLayer(
        l_conv1_left,
        name='pool1_left',
        pool_size=3,
        stride=2,
    )

    l_pool1_right = MaxPool1DLayer(
        l_conv1_right,
        name='pool1_right',
        pool_size=3,
        stride=2,
    )

    l_dropout_conv2_left = layers.DropoutLayer(
        l_pool1_left,
        name='drop_conv2_left',
        p=0.2,
    )

    l_dropout_conv2_right = layers.DropoutLayer(
        l_pool1_right,
        name='drop_conv2_right',
        p=0.2,
    )

    l_conv2_left = Conv1DLayer(
        l_dropout_conv2_left,
        name='conv2_left',
        num_filters=16,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_conv2_right = Conv1DLayer(
        l_dropout_conv2_right,
        name='conv2_right',
        num_filters=16,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_pool2_left = MaxPool1DLayer(
        l_conv2_left,
        name='pool2_left',
        pool_size=3,
        stride=2,
    )

    l_pool2_right = MaxPool1DLayer(
        l_conv2_right,
        name='pool2_right',
        pool_size=3,
        stride=2,
    )

    l_dropout_conv3_left = layers.DropoutLayer(
        l_pool2_left,
        name='drop_conv3_left',
        p=0.3,
    )

    l_dropout_conv3_right = layers.DropoutLayer(
        l_pool2_right,
        name='drop_conv3_right',
        p=0.3,
    )

    l_conv3_left = Conv1DLayer(
        l_dropout_conv3_left,
        name='conv3_left',
        num_filters=32,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_conv3_right = Conv1DLayer(
        l_dropout_conv3_right,
        name='conv3_right',
        num_filters=32,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_dropout_conv4_left = layers.DropoutLayer(
        l_conv3_left,
        name='drop_conv4_left',
        p=0.4,
    )

    l_dropout_conv4_right = layers.DropoutLayer(
        l_conv3_right,
        name='drop_conv4_right',
        p=0.4,
    )

    l_conv4_left = Conv1DLayer(
        l_dropout_conv4_left,
        name='conv4_left',
        num_filters=32,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_conv4_right = Conv1DLayer(
        l_dropout_conv4_right,
        name='conv4_right',
        num_filters=32,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_pool4_left = MaxPool1DLayer(
        l_conv4_left,
        name='pool4_left',
        pool_size=3,
        stride=2,
    )

    l_pool4_right = MaxPool1DLayer(
        l_conv4_right,
        name='pool4_right',
        pool_size=3,
        stride=2,
    )

    l_concat = layers.ConcatLayer(
        incomings=(l_pool4_left, l_pool4_right),
        name='concat',
    )

    l_dropout_dense1 = layers.DropoutLayer(
        l_concat,
        name='drop_dense1',
        p=0.5,
    )

    l_dense1 = layers.DenseLayer(
        l_dropout_dense1,
        name='dense1',
        num_units=128,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_dropout_dense2 = layers.DropoutLayer(
        l_dense1,
        name='drop_dense2',
        p=0.5,
    )

    l_dense2 = layers.DenseLayer(
        l_dropout_dense2,
        name='dense2',
        num_units=128,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_out = layers.DenseLayer(
        l_dense2,
        name='output',
        num_units=output_dim,
        nonlinearity=nonlinearities.sigmoid,
        W=init.Orthogonal(),
    )

    return l_out
